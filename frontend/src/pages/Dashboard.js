import { useState, useEffect } from "react";
import axios from "axios";
import { toast } from "sonner";
import { Database, Upload, Download, Key, Loader2, Search, Moon, Sun, FileText, Table as TableIcon } from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "../components/ui/dialog";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { useTheme } from "../components/ThemeProvider";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Dashboard() {
  const [singleUrl, setSingleUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [bulkLoading, setBulkLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [apiKeys, setApiKeys] = useState([]);
  const [newKeyName, setNewKeyName] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const [stats, setStats] = useState({ total: 0, success: 0, failed: 0 });
  const { theme, setTheme } = useTheme();

  useEffect(() => {
    fetchResults();
    fetchApiKeys();
  }, []);

  const fetchResults = async () => {
    try {
      const response = await axios.get(`${API}/results?limit=50`);
      setResults(response.data);
      
      // Calculate stats
      const total = response.data.length;
      const success = response.data.filter(r => r.status === "success").length;
      const failed = response.data.filter(r => r.status === "failed").length;
      setStats({ total, success, failed });
    } catch (error) {
      console.error("Error fetching results:", error);
    }
  };

  const fetchApiKeys = async () => {
    try {
      const response = await axios.get(`${API}/api-keys`);
      setApiKeys(response.data);
    } catch (error) {
      console.error("Error fetching API keys:", error);
    }
  };

  const handleSingleScrape = async () => {
    if (!singleUrl) {
      toast.error("Please enter a URL");
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API}/scrape`, { url: singleUrl });
      toast.success("Scraping completed successfully!");
      setResults(prev => [response.data, ...prev]);
      setSingleUrl("");
      fetchResults();
    } catch (error) {
      toast.error("Failed to scrape URL: " + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleBulkUpload = async () => {
    if (!selectedFile) {
      toast.error("Please select a CSV file");
      return;
    }

    setBulkLoading(true);
    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await axios.post(`${API}/scrape/upload-csv`, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      toast.success(`Successfully scraped ${response.data.total} URLs!`);
      setSelectedFile(null);
      fetchResults();
    } catch (error) {
      toast.error("Failed to process CSV: " + (error.response?.data?.detail || error.message));
    } finally {
      setBulkLoading(false);
    }
  };

  const handleExport = async (format) => {
    try {
      const response = await axios.get(`${API}/export/${format}`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `scraped_data.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success(`Exported as ${format.toUpperCase()}`);
    } catch (error) {
      toast.error("Export failed: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleCreateApiKey = async () => {
    if (!newKeyName) {
      toast.error("Please enter a key name");
      return;
    }

    try {
      const response = await axios.post(`${API}/api-keys`, { name: newKeyName });
      toast.success("API Key created successfully!");
      setNewKeyName("");
      fetchApiKeys();
      
      // Show the key to user
      navigator.clipboard.writeText(response.data.key);
      toast.info("API Key copied to clipboard!");
    } catch (error) {
      toast.error("Failed to create API key");
    }
  };

  const handleDeleteKey = async (keyId) => {
    try {
      await axios.delete(`${API}/api-keys/${keyId}`);
      toast.success("API Key deactivated");
      fetchApiKeys();
    } catch (error) {
      toast.error("Failed to delete API key");
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 backdrop-blur-xl bg-background/80 border-b border-border">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-md bg-primary flex items-center justify-center">
                <Database className="w-6 h-6 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-2xl font-extrabold tracking-tight" style={{ fontFamily: 'Manrope' }}>Startup Data Mine</h1>
                <p className="text-xs text-muted-foreground">Extract startup data from any URL</p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setTheme(theme === "light" ? "dark" : "light")}
              data-testid="theme-toggle-button"
            >
              {theme === "light" ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
            </Button>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <Card data-testid="total-scraped-card">
            <CardHeader className="pb-3">
              <CardDescription className="text-xs uppercase tracking-widest">Total Scraped</CardDescription>
              <CardTitle className="text-3xl font-extrabold" style={{ fontFamily: 'Manrope' }}>{stats.total}</CardTitle>
            </CardHeader>
          </Card>
          <Card data-testid="successful-card">
            <CardHeader className="pb-3">
              <CardDescription className="text-xs uppercase tracking-widest">Successful</CardDescription>
              <CardTitle className="text-3xl font-extrabold text-green-600" style={{ fontFamily: 'Manrope' }}>{stats.success}</CardTitle>
            </CardHeader>
          </Card>
          <Card data-testid="failed-card">
            <CardHeader className="pb-3">
              <CardDescription className="text-xs uppercase tracking-widest">Failed</CardDescription>
              <CardTitle className="text-3xl font-extrabold text-red-600" style={{ fontFamily: 'Manrope' }}>{stats.failed}</CardTitle>
            </CardHeader>
          </Card>
        </div>

        {/* Main Content */}
        <Tabs defaultValue="scrape" className="space-y-6">
          <TabsList className="grid w-full grid-cols-3 md:w-auto md:inline-grid">
            <TabsTrigger value="scrape" data-testid="scrape-tab">Scrape</TabsTrigger>
            <TabsTrigger value="results" data-testid="results-tab">Results</TabsTrigger>
            <TabsTrigger value="api" data-testid="api-tab">API Keys</TabsTrigger>
          </TabsList>

          {/* Scrape Tab */}
          <TabsContent value="scrape" className="space-y-6">
            {/* Single URL Scraping */}
            <Card data-testid="single-url-card">
              <CardHeader>
                <CardTitle style={{ fontFamily: 'Manrope' }}>Single URL Scraping</CardTitle>
                <CardDescription>Extract startup data from a single URL</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex gap-3">
                  <Input
                    placeholder="https://www.startupindia.gov.in/content/sih/en/profile..."
                    value={singleUrl}
                    onChange={(e) => setSingleUrl(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSingleScrape()}
                    className="flex-1"
                    data-testid="single-url-input"
                  />
                  <Button
                    onClick={handleSingleScrape}
                    disabled={loading}
                    className="min-w-[120px]"
                    data-testid="single-scrape-button"
                  >
                    {loading ? (
                      <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Scraping...</>
                    ) : (
                      <><Search className="w-4 h-4 mr-2" /> Scrape</>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Bulk CSV Upload */}
            <Card data-testid="bulk-upload-card">
              <CardHeader>
                <CardTitle style={{ fontFamily: 'Manrope' }}>Bulk CSV Upload</CardTitle>
                <CardDescription>Upload a CSV file with URLs to scrape multiple startups at once</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div
                    className="border-2 border-dashed border-border rounded-md p-8 text-center upload-zone cursor-pointer"
                    onClick={() => document.getElementById('csv-upload').click()}
                    data-testid="csv-upload-zone"
                  >
                    <Upload className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
                    <p className="text-sm text-muted-foreground mb-2">
                      {selectedFile ? selectedFile.name : "Click to upload or drag and drop"}
                    </p>
                    <p className="text-xs text-muted-foreground">CSV file with 'url' column</p>
                    <input
                      id="csv-upload"
                      type="file"
                      accept=".csv"
                      className="hidden"
                      onChange={(e) => setSelectedFile(e.target.files[0])}
                      data-testid="csv-file-input"
                    />
                  </div>
                  <Button
                    onClick={handleBulkUpload}
                    disabled={!selectedFile || bulkLoading}
                    className="w-full"
                    data-testid="bulk-scrape-button"
                  >
                    {bulkLoading ? (
                      <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Processing...</>
                    ) : (
                      <><Upload className="w-4 h-4 mr-2" /> Upload & Scrape</>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Results Tab */}
          <TabsContent value="results" className="space-y-6">
            <Card data-testid="results-card">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle style={{ fontFamily: 'Manrope' }}>Scraping Results</CardTitle>
                    <CardDescription>View and export all scraped data</CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleExport('csv')}
                      data-testid="export-csv-button"
                    >
                      <FileText className="w-4 h-4 mr-2" /> CSV
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleExport('json')}
                      data-testid="export-json-button"
                    >
                      <Download className="w-4 h-4 mr-2" /> JSON
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="data-table-container">
                  <table className="data-table" data-testid="results-table">
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Website</th>
                        <th>Email</th>
                        <th>Contact</th>
                        <th>Location</th>
                        <th>Industry</th>
                        <th>Stage</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {results.length === 0 ? (
                        <tr>
                          <td colSpan="8" className="text-center py-8 text-muted-foreground">
                            No results yet. Start scraping to see data here.
                          </td>
                        </tr>
                      ) : (
                        results.map((result) => (
                          <tr key={result.id} data-testid={`result-row-${result.id}`}>
                            <td>{result.name || '-'}</td>
                            <td>
                              {result.website ? (
                                <a href={result.website} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                                  {result.domain || result.website}
                                </a>
                              ) : '-'}
                            </td>
                            <td>{result.email || '-'}</td>
                            <td>{result.contact_number || result.mobile_number || '-'}</td>
                            <td>{result.location || '-'}</td>
                            <td>{result.focus_industry || '-'}</td>
                            <td>{result.stage || '-'}</td>
                            <td>
                              <span className={`status-badge ${result.status === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                                <span className={`status-dot ${result.status === 'success' ? 'bg-green-600' : 'bg-red-600'}`}></span>
                                {result.status}
                              </span>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* API Keys Tab */}
          <TabsContent value="api" className="space-y-6">
            <Card data-testid="api-keys-card">
              <CardHeader>
                <CardTitle style={{ fontFamily: 'Manrope' }}>API Key Management</CardTitle>
                <CardDescription>Create and manage API keys for programmatic access</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Create New Key */}
                <div className="flex gap-3">
                  <Input
                    placeholder="Key name (e.g., Production API)"
                    value={newKeyName}
                    onChange={(e) => setNewKeyName(e.target.value)}
                    className="flex-1"
                    data-testid="new-key-name-input"
                  />
                  <Button onClick={handleCreateApiKey} data-testid="create-key-button">
                    <Key className="w-4 h-4 mr-2" /> Create Key
                  </Button>
                </div>

                {/* API Keys List */}
                <div className="space-y-3">
                  {apiKeys.map((key) => (
                    <div key={key.id} className="flex items-center justify-between p-4 border border-border rounded-md" data-testid={`api-key-${key.id}`}>
                      <div className="flex-1">
                        <p className="font-medium" style={{ fontFamily: 'JetBrains Mono' }}>{key.name}</p>
                        <p className="text-sm text-muted-foreground font-mono">{key.key}</p>
                        <p className="text-xs text-muted-foreground mt-1">
                          Created: {new Date(key.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      <div className="flex items-center gap-3">
                        <Badge variant={key.is_active ? "default" : "secondary"}>
                          {key.is_active ? "Active" : "Inactive"}
                        </Badge>
                        {key.is_active && (
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => handleDeleteKey(key.id)}
                            data-testid={`delete-key-${key.id}`}
                          >
                            Deactivate
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                  {apiKeys.length === 0 && (
                    <p className="text-center text-muted-foreground py-8">No API keys yet. Create one to get started.</p>
                  )}
                </div>

                {/* API Documentation */}
                <div className="mt-6 p-4 bg-muted rounded-md">
                  <h4 className="font-semibold mb-2" style={{ fontFamily: 'Manrope' }}>API Usage Example</h4>
                  <pre className="text-xs overflow-x-auto" style={{ fontFamily: 'JetBrains Mono' }}>
{`curl -X POST "${BACKEND_URL}/api/protected/scrape" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"url": "https://example.com"}'`}
                  </pre>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}