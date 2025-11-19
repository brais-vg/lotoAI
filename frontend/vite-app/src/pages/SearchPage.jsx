import { useState } from "react";
import { api } from "../lib/api";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { Search, Loader2, FileText, Sparkles } from "lucide-react";
import { cn } from "../lib/utils";

export default function SearchPage() {
    const [query, setQuery] = useState("");
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(false);
    const [searched, setSearched] = useState(false);
    const [useAdvanced, setUseAdvanced] = useState(false);
    const [queryVariants, setQueryVariants] = useState([]);

    const handleSearch = async (e) => {
        e.preventDefault();
        if (!query.trim()) return;

        setLoading(true);
        setSearched(true);
        try {
            const data = await api.search.search(query, useAdvanced);
            setResults(data.results || []);
            setQueryVariants(data.query_variants || []);
        } catch (err) {
            console.error(err);
            setResults([]);
            setQueryVariants([]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex flex-col items-center justify-center space-y-4 py-10">
                <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
                    Search Knowledge Base
                </h1>
                <p className="text-muted-foreground text-lg max-w-2xl text-center">
                    Find information across all your uploaded documents using semantic search.
                </p>
                <form onSubmit={handleSearch} className="w-full max-w-lg space-y-3">
                    <div className="flex items-center space-x-2">
                        <Input
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="Search for anything..."
                            className="h-12 bg-input text-foreground placeholder:text-muted-foreground border-border focus:ring-primary"
                        />
                        <Button
                            type="submit"
                            size="lg"
                            disabled={loading}
                            className="bg-gradient-to-r from-primary to-accent hover:opacity-90"
                        >
                            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
                        </Button>
                    </div>

                    {/* Search Mode Toggle */}
                    <div className="flex items-center justify-center gap-2">
                        <Button
                            type="button"
                            variant={!useAdvanced ? "default" : "outline"}
                            size="sm"
                            onClick={() => setUseAdvanced(false)}
                            className={cn(
                                "transition-all",
                                !useAdvanced && "bg-gradient-to-r from-primary to-secondary"
                            )}
                        >
                            <Search className="h-3 w-3 mr-1" />
                            Normal
                        </Button>
                        <Button
                            type="button"
                            variant={useAdvanced ? "default" : "outline"}
                            size="sm"
                            onClick={() => setUseAdvanced(true)}
                            className={cn(
                                "transition-all",
                                useAdvanced && "bg-gradient-to-r from-secondary to-accent"
                            )}
                        >
                            <Sparkles className="h-3 w-3 mr-1" />
                            Advanced
                        </Button>
                    </div>
                </form>
            </div>

            {searched && (
                <div className="space-y-4">
                    <div className="flex items-center justify-between px-1">
                        <h2 className="text-xl font-semibold">
                            {results.length} Result{results.length !== 1 ? "s" : ""} found
                        </h2>
                        {useAdvanced && queryVariants.length > 0 && (
                            <div className="text-sm text-muted-foreground">
                                <Sparkles className="h-3 w-3 inline mr-1" />
                                {queryVariants.length} query variants used
                            </div>
                        )}
                    </div>

                    {/* Query Variants Display */}
                    {useAdvanced && queryVariants.length > 1 && (
                        <Card className="bg-card/50">
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm">Query Variants</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="flex flex-wrap gap-2">
                                    {queryVariants.map((variant, idx) => (
                                        <span
                                            key={idx}
                                            className="text-xs px-2 py-1 rounded-full bg-primary/10 text-primary border border-primary/20"
                                        >
                                            {variant}
                                        </span>
                                    ))}
                                </div>
                            </CardContent>
                        </Card>
                    )}

                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                        {results.map((result, idx) => (
                            <Card key={idx} className="overflow-hidden hover:shadow-lg hover:shadow-primary/20 transition-all">
                                <CardHeader className="pb-2">
                                    <CardTitle className="text-base flex items-center gap-2">
                                        <FileText className="h-4 w-4 text-primary" />
                                        <span className="truncate">{result.filename}</span>
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <p className="text-sm text-muted-foreground line-clamp-4">
                                        {result.chunk || "No content preview available."}
                                    </p>
                                    <div className="mt-4 flex items-center justify-between text-xs text-muted-foreground">
                                        <span>Score: {result.score?.toFixed(2)}</span>
                                        {result.created_at && (
                                            <span>{new Date(result.created_at).toLocaleDateString()}</span>
                                        )}
                                    </div>
                                    {useAdvanced && result.rrf_score && (
                                        <div className="mt-1 text-xs text-accent">
                                            RRF: {result.rrf_score.toFixed(3)}
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                    {results.length === 0 && !loading && (
                        <div className="text-center py-10 text-muted-foreground">
                            No results found for "{query}"
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
