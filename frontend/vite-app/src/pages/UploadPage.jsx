import { useState, useEffect } from "react";
import { api } from "../lib/api";
import { Button } from "../components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/Card";
import { Upload as UploadIcon, FileText, Loader2, RefreshCw } from "lucide-react";

export default function UploadPage() {
    const [uploads, setUploads] = useState([]);
    const [loading, setLoading] = useState(false);
    const [uploading, setUploading] = useState(false);

    const loadUploads = async () => {
        setLoading(true);
        try {
            const data = await api.upload.list();
            setUploads(data.items || []);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadUploads();
    }, []);

    const handleFileChange = async (e) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setUploading(true);
        try {
            const result = await api.upload.uploadFile(file);
            
            // Check indexing status
            if (result?.indexing && !result.indexing.success) {
                const errorMsg = result.indexing.error || "No se pudo indexar el contenido";
                alert(`⚠️ Archivo subido pero con advertencia:\n${errorMsg}\n\nEl documento podría no ser buscable por contenido.`);
            }
            
            await loadUploads();
        } catch (err) {
            console.error(err);
            alert("Upload failed");
        } finally {
            setUploading(false);
            e.target.value = ""; // Reset input
        }
    };

    return (
        <div className="space-y-6">
            <Card>
                <CardHeader>
                    <CardTitle>Upload Documents</CardTitle>
                    <CardDescription>Upload files to be indexed for RAG search.</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="flex items-center justify-center w-full">
                        <label
                            htmlFor="dropzone-file"
                            className="flex flex-col items-center justify-center w-full h-64 border-2 border-dashed rounded-lg cursor-pointer hover:bg-accent/50 transition-colors"
                        >
                            <div className="flex flex-col items-center justify-center pt-5 pb-6">
                                {uploading ? (
                                    <Loader2 className="w-10 h-10 mb-3 animate-spin text-muted-foreground" />
                                ) : (
                                    <UploadIcon className="w-10 h-10 mb-3 text-muted-foreground" />
                                )}
                                <p className="mb-2 text-sm text-muted-foreground">
                                    <span className="font-semibold">Click to upload</span> or drag and drop
                                </p>
                                <p className="text-xs text-muted-foreground">PDF, TXT, MD (MAX. 10MB)</p>
                            </div>
                            <input
                                id="dropzone-file"
                                type="file"
                                className="hidden"
                                onChange={handleFileChange}
                                disabled={uploading}
                            />
                        </label>
                    </div>
                </CardContent>
            </Card>

            <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                    <CardTitle>Recent Uploads</CardTitle>
                    <Button variant="ghost" size="icon" onClick={loadUploads} disabled={loading}>
                        <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
                    </Button>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        {uploads.length === 0 && !loading && (
                            <div className="text-center text-muted-foreground py-4">No uploads yet</div>
                        )}
                        {uploads.map((file) => (
                            <div
                                key={file.id}
                                className="flex items-center justify-between p-4 rounded-lg border bg-card/50"
                            >
                                <div className="flex items-center gap-4">
                                    <div className="p-2 bg-primary/10 rounded-full">
                                        <FileText className="h-5 w-5 text-primary" />
                                    </div>
                                    <div>
                                        <p className="font-medium">{file.filename}</p>
                                        <p className="text-xs text-muted-foreground">
                                            {new Date(file.created_at).toLocaleString()} • {(file.size_bytes / 1024).toFixed(1)} KB
                                        </p>
                                    </div>
                                </div>
                                <div className="text-xs text-muted-foreground bg-secondary px-2 py-1 rounded">
                                    {file.content_type}
                                </div>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
