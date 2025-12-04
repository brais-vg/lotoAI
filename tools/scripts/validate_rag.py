"""
RAG Validation Script - Tests RAG improvements with synthetic PDFs.
Compares performance with and without reranking.
"""

import json
import requests
import time
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


class RAGTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = []
        
    def upload_test_pdfs(self, pdf_dir: str = "./test_pdfs") -> List[Dict]:
        """Upload all test PDFs to RAG server."""
        pdf_path = Path(pdf_dir)
        if not pdf_path.exists():
            print("❌ Test PDFs directory not found. Run generate_test_pdfs.py first.")
            return []
        
        uploaded = []
        pdfs = list(pdf_path.glob("*.pdf"))
        
        print(f"\n📤 Uploading {len(pdfs)} test PDFs...")
        for pdf_file in pdfs:
            try:
                with open(pdf_file, 'rb') as f:
                    files = {'file': (pdf_file.name, f, 'application/pdf')}
                    response = requests.post(f"{self.base_url}/upload", files=files)
                    
                if response.status_code == 200:
                    data = response.json()
                    uploaded.append(data)
                    print(f"  ✓ {pdf_file.name} - ID: {data['id']}")
                else:
                    print(f"  ✗ {pdf_file.name} - Error: {response.status_code}")
            except Exception as e:
                print(f"  ✗ {pdf_file.name} - Exception: {e}")
        
        # Wait for indexing to complete
        print("\n⏳ Waiting 10 seconds for indexing to complete...")
        time.sleep(10)
        
        return uploaded
    
    def run_query(self, query: str, rerank: bool = True, endpoint: str = "/search") -> Dict:
        """Execute a search query."""
        url = f"{self.base_url}{endpoint}"
        payload = {"text": query, "limit": 10, "rerank": rerank}
        
        start_time = time.time()
        response = requests.post(url, json=payload)
        elapsed = (time.time() - start_time) * 1000  # Convert to ms
        
        if response.status_code == 200:
            data = response.json()
            data['elapsed_ms'] = elapsed
            return data
        else:
            return {"error": f"HTTP {response.status_code}", "elapsed_ms": elapsed}
    
    def test_single_query(self, query_data: Dict) -> Dict[str, Any]:
        """Test a single query with and without reranking."""
        query = query_data["query"]
        print(f"\n🔍 Testing: {query}")
        
        # Test without reranking
        result_no_rerank = self.run_query(query, rerank=False)
        time.sleep(0.5)  # Brief pause between requests
        
        # Test with reranking
        result_with_rerank = self.run_query(query, rerank=True)
        
        # Compare results
        comparison = {
            "query": query,
            "category": query_data.get("category"),
            "expected_doc": query_data.get("expected_doc"),
            "expected_answer": query_data.get("expected_answer"),
            "without_rerank": {
                "mode": result_no_rerank.get("mode"),
                "elapsed_ms": result_no_rerank.get("elapsed_ms"),
                "num_results": len(result_no_rerank.get("results", [])),
                "top_result": result_no_rerank.get("results", [{}])[0] if result_no_rerank.get("results") else None
            },
            "with_rerank": {
                "mode": result_with_rerank.get("mode"),
                "elapsed_ms": result_with_rerank.get("elapsed_ms"),
                "num_results": len(result_with_rerank.get("results", [])),
                "top_result": result_with_rerank.get("results", [{}])[0] if result_with_rerank.get("results") else None
            }
        }
        
        # Check if reranking changed order
        if (comparison["without_rerank"]["top_result"] and 
            comparison["with_rerank"]["top_result"]):
            
            top_no_rerank = comparison["without_rerank"]["top_result"].get("filename")
            top_with_rerank = comparison["with_rerank"]["top_result"].get("filename")
            comparison["order_changed"] = (top_no_rerank != top_with_rerank)
            
            # Check rerank score impact
            if "rerank_score" in comparison["with_rerank"]["top_result"]:
                comparison["rerank_score"] = comparison["with_rerank"]["top_result"]["rerank_score"]
                comparison["original_score"] = comparison["with_rerank"]["top_result"].get("original_score")
        
        self.results.append(comparison)
        
        # Print summary
        print(f"  Without reranking: {comparison['without_rerank']['mode']} - {comparison['without_rerank']['elapsed_ms']:.1f}ms")
        print(f"  With reranking:    {comparison['with_rerank']['mode']} - {comparison['with_rerank']['elapsed_ms']:.1f}ms")
        if comparison.get("order_changed"):
            print(f"  📊 Reranking changed top result!")
        
        return comparison
    
    def run_all_tests(self, queries_file: str = "./test_queries.json"):
        """Run all test queries."""
        try:
            with open(queries_file, 'r') as f:
                test_data = json.load(f)
        except FileNotFoundError:
            print(f"❌ Test queries file not found: {queries_file}")
            return
        
        queries = test_data.get("test_queries", [])
        print(f"\n🧪 Running {len(queries)} test queries...")
        
        for i, query_data in enumerate(queries, 1):
            print(f"\n[{i}/{len(queries)}]")
            self.test_single_query(query_data)
            time.sleep(0.5)  # Brief pause between tests
        
        # Generate report
        self.generate_report()
    
    def generate_report(self):
        """Generate a test report."""
        if not self.results:
            print("\n❌ No test results to report")
            return
        
        print("\n" + "="*80)
        print("📊 RAG VALIDATION REPORT")
        print("="*80)
        
        # Summary statistics
        total = len(self.results)
        order_changed = sum(1 for r in self.results if r.get("order_changed"))
        
        avg_latency_no_rerank = sum(r["without_rerank"]["elapsed_ms"] for r in self.results) / total
        avg_latency_with_rerank = sum(r["with_rerank"]["elapsed_ms"] for r in self.results) / total
        rerank_overhead = avg_latency_with_rerank - avg_latency_no_rerank
        
        print(f"\nTotal Queries: {total}")
        print(f"Results Reordered by Reranking: {order_changed} ({order_changed/total*100:.1f}%)")
        print(f"\nAverage Latency:")
        print(f"  Without Reranking: {avg_latency_no_rerank:.1f}ms")
        print(f"  With Reranking:    {avg_latency_with_rerank:.1f}ms")
        print(f"  Reranking Overhead: {rerank_overhead:.1f}ms")
        
        # Category breakdown
        print(f"\nResults by Category:")
        categories = {}
        for result in self.results:
            cat = result.get("category", "unknown")
            if cat not in categories:
                categories[cat] = {"total": 0, "reordered": 0}
            categories[cat]["total"] += 1
            if result.get("order_changed"):
                categories[cat]["reordered"] += 1
        
        for cat, stats in sorted(categories.items()):
            reorder_pct = stats["reordered"] / stats["total"] * 100 if stats["total"] > 0 else 0
            print(f"  {cat}: {stats['reordered']}/{stats['total']} reordered ({reorder_pct:.0f}%)")
        
        # Top reranking impacts
        rerank_impacts = [r for r in self.results if r.get("rerank_score") and r.get("original_score")]
        if rerank_impacts:
            rerank_impacts.sort(key=lambda x: abs(x["rerank_score"] - x["original_score"]), reverse=True)
            print(f"\nTop 5 Reranking Impacts:")
            for i, r in enumerate(rerank_impacts[:5], 1):
                delta = r["rerank_score"] - r["original_score"]
                print(f"  {i}. {r['query'][:60]}...")
                print(f"     Score change: {r['original_score']:.3f} → {r['rerank_score']:.3f} (Δ{delta:+.3f})")
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"rag_test_results_{timestamp}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": timestamp,
                "summary": {
                    "total_queries": total,
                    "reordered_count": order_changed,
                    "avg_latency_no_rerank_ms": avg_latency_no_rerank,
                    "avg_latency_with_rerank_ms": avg_latency_with_rerank,
                    "rerank_overhead_ms": rerank_overhead
                },
                "detailed_results": self.results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Detailed results saved to: {output_file}")
        print("="*80)


def main():
    """Main test execution."""
    print("🚀 RAG Validation Suite")
    print("="*80)
    
    tester = RAGTester()
    
    # Step 1: Upload test PDFs
    uploaded = tester.upload_test_pdfs()
    if not uploaded:
        print("\n⚠️  No PDFs uploaded. Generate them first with generate_test_pdfs.py")
        return
    
    print(f"\n✓ Successfully uploaded {len(uploaded)} test documents")
    
    # Step 2: Run validation tests
    tester.run_all_tests()
    
    print("\n✅ Validation complete!")


if __name__ == "__main__":
    main()
