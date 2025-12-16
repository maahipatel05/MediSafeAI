// import { useState, useEffect } from "react";
// import "./App.css"; // Changed from @/App.css to standard relative path for safety
// import { BrowserRouter, Routes, Route } from "react-router-dom";
// import axios from "axios";
// import { Toaster, toast } from "sonner";
// import { Search, Clock, AlertCircle, CheckCircle, BarChart3, Zap, Shield, Award, Target, Sparkles, Brain, Database, Plus, X, Download } from "lucide-react";
// import { Button } from "./components/ui/button";
// import { Input } from "./components/ui/input";
// import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
// import { Badge } from "./components/ui/badge";
// import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "./components/ui/accordion";
// import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
// import { ScrollArea } from "./components/ui/scroll-area";
// import { Progress } from "./components/ui/progress";

// // Import new components
// import SystemArchitecture from "./components/SystemArchitecture";
// import EvaluationTab from "./components/EvaluationTab";

// // FORCE PORT 8001 for Local Setup
// const API_BASE = "http://localhost:8001/api";

// const Home = () => {
//   const [query, setQuery] = useState("");
//   const [loading, setLoading] = useState(false);
//   const [loadingStage, setLoadingStage] = useState("");
//   const [progress, setProgress] = useState(0);
//   const [result, setResult] = useState(null);
//   const [history, setHistory] = useState([]);
//   const [stats, setStats] = useState(null);
//   const [activeTab, setActiveTab] = useState("query");
//   const [compareQueries, setCompareQueries] = useState([]);

//   useEffect(() => {
//     fetchHistory();
//     fetchStats();
//     document.documentElement.classList.add('dark');
//   }, []);

//   const fetchHistory = async () => {
//     try {
//       const response = await axios.get(`${API_BASE}/history?limit=20`);
//       setHistory(response.data);
//     } catch (error) {
//       console.error("Error fetching history:", error);
//     }
//   };

//   const fetchStats = async () => {
//     try {
//       const response = await axios.get(`${API_BASE}/stats`);
//       setStats(response.data);
//     } catch (error) {
//       console.error("Error fetching stats:", error);
//     }
//   };

//   const simulateProgress = () => {
//     const stages = [
//       { progress: 20, text: "Expanding query keywords..." },
//       { progress: 40, text: "Scanning local FAISS index..." },
//       { progress: 60, text: "Retrieving top evidence..." },
//       { progress: 80, text: "Generating answer locally..." },
//       { progress: 95, text: "Finalizing risk score..." }
//     ];
//     let currentStage = 0;
//     const interval = setInterval(() => {
//       if (currentStage < stages.length) {
//         setProgress(stages[currentStage].progress);
//         setLoadingStage(stages[currentStage].text);
//         currentStage++;
//       } else {
//         clearInterval(interval);
//       }
//     }, 800); // Faster for local
//     return interval;
//   };

//   const handleSubmit = async (e) => {
//     e.preventDefault();
//     if (!query.trim()) {
//       toast.error("Please enter a question");
//       return;
//     }

//     setLoading(true);
//     setResult(null);
//     setProgress(0);
//     setLoadingStage("Initializing Local LLM...");

//     const progressInterval = simulateProgress();

//     try {
//       const response = await axios.post(`${API_BASE}/query`, {
//         query: query,
//         user_id: "local-user"
//       });
      
//       clearInterval(progressInterval);
//       setProgress(100);
//       setLoadingStage("Complete!");
      
//       setTimeout(() => {
//         setResult(response.data);
//         toast.success("✅ Analysis complete!");
//         fetchHistory();
//         fetchStats();
//         setActiveTab("result");
//       }, 500);
//     } catch (error) {
//       clearInterval(progressInterval);
//       console.error("Error:", error);
//       toast.error("❌ Connection Failed. Is backend running on 8001?");
//     } finally {
//       setTimeout(() => {
//         setLoading(false);
//         setProgress(0);
//       }, 1000);
//     }
//   };

//   const addToComparison = (item) => {
//     if (compareQueries.length >= 3) return toast.error("Max 3 items");
//     if (compareQueries.find(q => q.id === item.id)) return toast.error("Already added");
//     setCompareQueries([...compareQueries, item]);
//     toast.success("Added to comparison");
//   };

//   const removeFromComparison = (id) => {
//     setCompareQueries(compareQueries.filter(q => q.id !== id));
//   };

//   const exportToPDF = () => {
//       if (!result) return;
//       const content = `MEDISAFE LOCAL REPORT\nQuery: ${result.query}\nResponse: ${result.response}`;
//       const blob = new Blob([content], { type: 'text/plain' });
//       const url = URL.createObjectURL(blob);
//       const a = document.createElement('a');
//       a.href = url;
//       a.download = `Report-${Date.now()}.txt`;
//       document.body.appendChild(a);
//       a.click();
//       document.body.removeChild(a);
//   };

//   const getRiskColor = (risk) => {
//     const colors = {
//       "CRITICAL": "bg-red-600",
//       "HIGH": "bg-orange-600",
//       "MODERATE": "bg-yellow-600",
//       "LOW": "bg-green-600"
//     };
//     return colors[risk] || "bg-gray-600";
//   };

//   return (
//     <div className="min-h-screen bg-gray-900 text-white transition-all duration-500">
//       <Toaster position="top-center" richColors />
      
//       {/* Header */}
//       <header className="bg-gray-900 border-b border-gray-800 sticky top-0 z-50">
//         <div className="container mx-auto px-6 py-4 flex items-center justify-between">
//           <div className="flex items-center gap-4">
//             <div className="bg-blue-600 p-2 rounded-lg">
//               <Database className="h-8 w-8 text-white" />
//             </div>
//             <div>
//               <h1 className="text-2xl font-bold tracking-tight">MediSafe AI</h1>
//               <div className="flex items-center gap-2">
//                 <Badge variant="outline" className="text-xs border-green-500 text-green-500">Local Mode</Badge>
//                 <span className="text-xs text-gray-400">FLAN-T5-Large Model</span>
//               </div>
//             </div>
//           </div>
//         </div>

//         {/* Navigation */}
//         <div className="border-t border-gray-800 bg-gray-900/50 backdrop-blur-md">
//           <div className="container mx-auto px-6">
//             <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
//               <TabsList className="bg-transparent border-b border-transparent w-full justify-start h-12 p-0">
//                 {['query', 'result', 'history', 'compare', 'evaluation', 'architecture'].map(tab => (
//                   <TabsTrigger 
//                     key={tab}
//                     value={tab} 
//                     className="capitalize data-[state=active]:border-b-2 data-[state=active]:border-blue-500 rounded-none px-6 h-full"
//                   >
//                     {tab}
//                   </TabsTrigger>
//                 ))}
//               </TabsList>
//             </Tabs>
//           </div>
//         </div>
//       </header>

//       {/* Main Content */}
//       <main className="container mx-auto px-4 py-8">
//         <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-8">

//           {/* QUERY TAB */}
//           <TabsContent value="query" className="space-y-8">
//             <Card className="max-w-4xl mx-auto bg-gray-800 border-gray-700">
//               <CardHeader>
//                 <CardTitle className="text-3xl text-center bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
//                   Local Drug Intelligence
//                 </CardTitle>
//                 <CardDescription className="text-center text-gray-400">
//                   Secure, private, and running completely on your device.
//                 </CardDescription>
//               </CardHeader>
//               <CardContent>
//                 <form onSubmit={handleSubmit} className="space-y-6">
//                   <div className="relative">
//                     <Input
//                       placeholder="e.g., Interactions between Aspirin and Warfarin?"
//                       value={query}
//                       onChange={(e) => setQuery(e.target.value)}
//                       className="h-14 text-lg pl-12 bg-gray-900 border-gray-600 focus:border-blue-500"
//                       disabled={loading}
//                     />
//                     <Search className="absolute left-4 top-4 h-6 w-6 text-gray-500" />
//                   </div>

//                   {loading && (
//                     <div className="space-y-2">
//                       <div className="flex justify-between text-sm text-blue-400">
//                         <span>{loadingStage}</span>
//                         <span>{progress}%</span>
//                       </div>
//                       <Progress value={progress} className="h-2 bg-gray-700" />
//                     </div>
//                   )}

//                   <Button type="submit" className="w-full h-12 text-lg bg-blue-600 hover:bg-blue-700" disabled={loading}>
//                     {loading ? "Analyzing..." : "Analyze Interaction"}
//                   </Button>
//                 </form>
//               </CardContent>
//             </Card>

//             {/* Quick Stats */}
//             {stats && (
//               <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
//                 <Card className="bg-gray-800 border-gray-700 p-4 text-center">
//                    <p className="text-3xl font-bold text-white">{stats.total_queries}</p>
//                    <p className="text-sm text-gray-400">Total Queries</p>
//                 </Card>
//                 <Card className="bg-gray-800 border-gray-700 p-4 text-center">
//                    <p className="text-3xl font-bold text-blue-400">Local</p>
//                    <p className="text-sm text-gray-400">System Type</p>
//                 </Card>
//               </div>
//             )}
//           </TabsContent>

//           {/* RESULT TAB */}
//           <TabsContent value="result">
//             {result ? (
//               <div className="max-w-4xl mx-auto space-y-6">
//                 <div className="flex justify-end gap-2">
//                     <Button variant="outline" onClick={() => addToComparison(result)}><Plus className="mr-2 h-4 w-4"/> Compare</Button>
//                     <Button variant="secondary" onClick={exportToPDF}><Download className="mr-2 h-4 w-4"/> Save</Button>
//                 </div>

//                 <Card className="bg-gray-800 border-gray-700">
//                     <CardHeader>
//                         <div className="flex justify-between items-center">
//                             <CardTitle>Analysis Result</CardTitle>
//                             <Badge className={`${getRiskColor(result.risk_score)} text-lg px-4 py-1`}>
//                                 {result.risk_score} RISK
//                             </Badge>
//                         </div>
//                     </CardHeader>
//                     <CardContent className="space-y-6">
//                         <div className="bg-gray-900 p-4 rounded-lg">
//                             <p className="text-gray-300 font-mono text-sm mb-2">QUERY</p>
//                             <p className="text-xl font-medium">{result.query}</p>
//                         </div>

//                         <div>
//                             <p className="text-gray-300 font-mono text-sm mb-2">AI RESPONSE (FLAN-T5)</p>
//                             <div className="prose prose-invert max-w-none">
//                                 <p className="whitespace-pre-wrap leading-relaxed">{result.response}</p>
//                             </div>
//                         </div>

//                         {result.citations?.length > 0 && (
//                             <div>
//                                 <p className="text-gray-300 font-mono text-sm mb-3">EVIDENCE ({result.citations.length})</p>
//                                 <Accordion type="single" collapsible>
//                                     {result.citations.map((c, i) => (
//                                         <AccordionItem key={i} value={`item-${i}`} className="border-gray-700">
//                                             <AccordionTrigger className="hover:no-underline">
//                                                 <div className="flex gap-4 text-sm">
//                                                     <Badge variant="outline">{c.source}</Badge>
//                                                     <span>{c.drug_name}</span>
//                                                 </div>
//                                             </AccordionTrigger>
//                                             <AccordionContent className="text-gray-400 bg-gray-900/50 p-4 rounded">
//                                                 {c.text || "No preview text available."}
//                                             </AccordionContent>
//                                         </AccordionItem>
//                                     ))}
//                                 </Accordion>
//                             </div>
//                         )}
//                     </CardContent>
//                 </Card>
//               </div>
//             ) : (
//                 <div className="text-center py-20 text-gray-500">No analysis available. Run a query first.</div>
//             )}
//           </TabsContent>

//           {/* HISTORY TAB */}
//           <TabsContent value="history">
//             <Card className="max-w-4xl mx-auto bg-gray-800 border-gray-700">
//                 <CardHeader><CardTitle>Query History</CardTitle></CardHeader>
//                 <CardContent>
//                     <ScrollArea className="h-[500px]">
//                         {history.map((h, i) => (
//                             <div key={i} className="mb-4 p-4 bg-gray-900 rounded border border-gray-800 flex justify-between items-center">
//                                 <div>
//                                     <p className="font-bold">{h.query}</p>
//                                     <p className="text-xs text-gray-400">{new Date(h.timestamp).toLocaleString()}</p>
//                                 </div>
//                                 <Badge className={getRiskColor(h.risk_score)}>{h.risk_score}</Badge>
//                             </div>
//                         ))}
//                     </ScrollArea>
//                 </CardContent>
//             </Card>
//           </TabsContent>

//           {/* COMPARE TAB */}
//           <TabsContent value="compare">
//              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
//                  {compareQueries.map((q, i) => (
//                      <Card key={i} className="bg-gray-800 border-gray-700">
//                          <CardHeader>
//                             <div className="flex justify-between">
//                                 <Badge className={getRiskColor(q.risk_score)}>{q.risk_score}</Badge>
//                                 <Button variant="ghost" size="icon" onClick={() => removeFromComparison(q.id)}><X className="h-4 w-4"/></Button>
//                             </div>
//                          </CardHeader>
//                          <CardContent>
//                              <p className="font-bold mb-2">{q.query}</p>
//                              <p className="text-sm text-gray-400 line-clamp-6">{q.response}</p>
//                          </CardContent>
//                      </Card>
//                  ))}
//                  {compareQueries.length === 0 && <div className="col-span-3 text-center py-20">Add items from History or Results to compare</div>}
//              </div>
//           </TabsContent>

//           {/* EVALUATION TAB */}
//           <TabsContent value="evaluation">
//             <EvaluationTab />
//           </TabsContent>

//           {/* ARCHITECTURE TAB */}
//           <TabsContent value="architecture">
//             <SystemArchitecture />
//           </TabsContent>

//         </Tabs>
//       </main>

//       {/* Footer */}
//       <footer className="border-t border-gray-800 mt-12 py-8 bg-gray-900">
//         <div className="container mx-auto px-4 text-center text-gray-500 text-sm">
//           <p className="mb-2">MediSafe AI (Local Edition)</p>
//           <p>Powered by DrugBank Data & Google FLAN-T5</p>
//         </div>
//       </footer>
//     </div>
//   );
// };

// function App() {
//   return (
//     <BrowserRouter>
//       <Routes>
//         <Route path="/" element={<Home />} />
//       </Routes>
//     </BrowserRouter>
//   );
// }

// export default App;


import { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import axios from "axios";
import { Toaster, toast } from "sonner";
import { Activity, Search, Clock, AlertCircle, CheckCircle, FileText, TrendingUp, Download, Plus, X, BarChart3, Zap, Shield, Award, Target, Sparkles, Info, Brain, Microscope, Database, Layers, Network, Sun, Moon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import SystemArchitecture from "@/components/SystemArchitecture";
import EvaluationTab from "@/components/EvaluationTab";

const API = "http://localhost:8001/api";

const Home = () => {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingStage, setLoadingStage] = useState("");
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [stats, setStats] = useState(null);
  const [activeTab, setActiveTab] = useState("query");
  const [compareQueries, setCompareQueries] = useState([]);
  const [darkMode, setDarkMode] = useState(true);
  const [showHelp, setShowHelp] = useState(false);

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
    if (darkMode) {
      document.documentElement.classList.remove('dark');
    } else {
      document.documentElement.classList.add('dark');
    }
  };

  useEffect(() => {
    fetchHistory();
    fetchStats();
    // Always use dark theme
    document.documentElement.classList.add('dark');
  }, []);

  const fetchHistory = async () => {
    try {
      const response = await axios.get(`${API}/history?limit=20`);
      setHistory(response.data);
    } catch (error) {
      console.error("Error fetching history:", error);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/stats`);
      setStats(response.data);
    } catch (error) {
      console.error("Error fetching stats:", error);
    }
  };

  const simulateProgress = () => {
    const stages = [
      { progress: 20, text: "Understanding your question..." },
      { progress: 40, text: "Searching medical database..." },
      { progress: 60, text: "Analyzing drug interactions..." },
      { progress: 80, text: "Verifying with sources..." },
      { progress: 95, text: "Preparing your answer..." }
    ];

    let currentStage = 0;
    const interval = setInterval(() => {
      if (currentStage < stages.length) {
        setProgress(stages[currentStage].progress);
        setLoadingStage(stages[currentStage].text);
        currentStage++;
      } else {
        clearInterval(interval);
      }
    }, 5000);

    return interval;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) {
      toast.error("Please enter a question about drug interactions");
      return;
    }

    setLoading(true);
    setResult(null);
    setProgress(0);
    setLoadingStage("Starting analysis...");

    const progressInterval = simulateProgress();

    try {
      const response = await axios.post(`${API}/query`, {
        query: query,
        user_id: "anonymous"
      });
      
      clearInterval(progressInterval);
      setProgress(100);
      setLoadingStage("Complete!");
      
      setTimeout(() => {
        setResult(response.data);
        toast.success("✅ Analysis complete!", {
          description: "Your results are ready to view"
        });
        fetchHistory();
        fetchStats();
        setActiveTab("result");
      }, 500);
    } catch (error) {
      clearInterval(progressInterval);
      console.error("Error processing query:", error);
      toast.error("❌ Something went wrong", {
        description: "Please try again or rephrase your question"
      });
    } finally {
      setTimeout(() => {
        setLoading(false);
        setProgress(0);
        setLoadingStage("");
      }, 1000);
    }
  };

  const addToComparison = (item) => {
    if (compareQueries.length >= 3) {
      toast.error("Maximum 3 queries can be compared");
      return;
    }
    if (compareQueries.find(q => q.id === item.id)) {
      toast.error("Query already added to comparison");
      return;
    }
    setCompareQueries([...compareQueries, item]);
    toast.success("Added to comparison");
  };

  const removeFromComparison = (id) => {
    setCompareQueries(compareQueries.filter(q => q.id !== id));
  };

  const exportToPDF = () => {
    if (!result) {
      toast.error("No result to export");
      return;
    }
    
    const content = `
╔════════════════════════════════════════════════════════╗
║          MEDISAFE AI - ANALYSIS REPORT                 ║
╚════════════════════════════════════════════════════════╝

📋 YOUR QUESTION:
${result.query}

⚠️  RISK ASSESSMENT: ${result.risk_score}
✅ CONFIDENCE SCORE: ${(result.grounding_score * 100).toFixed(0)}%
📚 SOURCES CONSULTED: ${result.citations?.length || 0}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 DETAILED ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

${result.response}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📖 MEDICAL SOURCES & EVIDENCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

${result.citations.map((c, i) => `
[${i + 1}] ${c.drug_name}
    Database: ${c.source}
    Relevance: ${(c.relevance_score * 100).toFixed(1)}%
    `).join('\n')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 QUERY BREAKDOWN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Your question was broken down into ${result.sub_queries?.length || 0} focused queries:
${result.sub_queries?.map((sq, i) => `${i + 1}. ${sq}`).join('\n') || 'N/A'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  IMPORTANT DISCLAIMER:
This analysis is for informational purposes only and should not
replace professional medical advice. Always consult with qualified
healthcare professionals before making medication decisions.

📅 Generated: ${new Date().toLocaleString()}
🏥 Powered by: MediSafe AI + DrugBank Database
🤖 AI Model: Google Gemini 2.5 Pro

════════════════════════════════════════════════════════
`;
    
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `MediSafe-Report-${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success("📄 Report downloaded successfully!");
  };

  const getRiskColor = (risk) => {
    const colors = {
      "CRITICAL": "bg-gradient-to-r from-red-500 to-red-600 text-white",
      "HIGH": "bg-gradient-to-r from-orange-500 to-orange-600 text-white",
      "MODERATE": "bg-gradient-to-r from-yellow-500 to-yellow-600 text-white",
      "LOW": "bg-gradient-to-r from-green-500 to-green-600 text-white"
    };
    return colors[risk] || "bg-gradient-to-r from-gray-500 to-gray-600 text-white";
  };

  const getRiskIcon = (risk) => {
    if (risk === "CRITICAL") return <AlertCircle className="h-6 w-6" />;
    if (risk === "HIGH") return <AlertCircle className="h-6 w-6" />;
    if (risk === "LOW") return <CheckCircle className="h-6 w-6" />;
    return <Shield className="h-6 w-6" />;
  };

  const getRiskDescription = (risk) => {
    const descriptions = {
      "CRITICAL": "Dangerous combination - Seek immediate medical advice",
      "HIGH": "Significant interaction - Consult healthcare provider",
      "MODERATE": "Monitor carefully - May require dose adjustment",
      "LOW": "Minimal interaction - Generally safe"
    };
    return descriptions[risk] || "Unknown risk level";
  };

  return (
    <div className={`min-h-screen transition-all duration-500 ${darkMode ? 'dark bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900' : 'bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50'}`}>
      <Toaster position="top-center" richColors expand={true} />
      
      {/* Professional Header */}
      <header className="bg-gradient-to-r from-gray-900 via-blue-900/20 to-gray-900 border-b-2 border-blue-500/30">
        <div className="container mx-auto px-6 py-6">
          <div className="flex items-center gap-6">
            {/* Logo - Hexagon Medical Design */}
            <div className="relative">
              <div className="absolute inset-0 bg-blue-500 blur-xl opacity-30"></div>
              <div className="relative bg-gradient-to-br from-blue-600 to-blue-800 p-5 rounded-2xl shadow-2xl border-2 border-blue-400/30">
                <Database className="h-12 w-12 text-white" />
              </div>
            </div>
            <div>
              <h1 className="text-5xl font-extrabold text-white tracking-tight" style={{fontFamily: 'system-ui, -apple-system, sans-serif', letterSpacing: '-0.02em'}}>
                MediSafe AI
              </h1>
              <p className="text-lg text-blue-200 font-semibold mt-1.5">
                Clinical Drug Safety Intelligence
              </p>
            </div>
          </div>
        </div>

        {/* Navigation Bar - Right after header */}
        <div className="bg-gray-800/50 border-t border-gray-700">
          <div className="container mx-auto px-6">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid w-full grid-cols-6 h-14 bg-transparent border-0 gap-0">
                <TabsTrigger 
                  value="query" 
                  data-testid="tab-query" 
                  className="text-base font-semibold border-r border-gray-700 rounded-none data-[state=active]:bg-blue-600 data-[state=active]:text-white transition-all"
                >
                  Query
                </TabsTrigger>
                <TabsTrigger 
                  value="result" 
                  data-testid="tab-result" 
                  className="text-base font-semibold border-r border-gray-700 rounded-none data-[state=active]:bg-purple-600 data-[state=active]:text-white transition-all"
                >
                  Results
                </TabsTrigger>
                <TabsTrigger 
                  value="history" 
                  data-testid="tab-history" 
                  className="text-base font-semibold border-r border-gray-700 rounded-none data-[state=active]:bg-cyan-600 data-[state=active]:text-white transition-all"
                >
                  History
                </TabsTrigger>
                <TabsTrigger 
                  value="compare" 
                  data-testid="tab-compare" 
                  className="text-base font-semibold border-r border-gray-700 rounded-none data-[state=active]:bg-green-600 data-[state=active]:text-white transition-all"
                >
                  Compare {compareQueries.length > 0 && `(${compareQueries.length})`}
                </TabsTrigger>
                <TabsTrigger 
                  value="evaluation" 
                  data-testid="tab-evaluation" 
                  className="text-base font-semibold border-r border-gray-700 rounded-none data-[state=active]:bg-indigo-600 data-[state=active]:text-white transition-all"
                >
                  Evaluation
                </TabsTrigger>
                <TabsTrigger 
                  value="architecture" 
                  data-testid="tab-architecture" 
                  className="text-base font-semibold rounded-none data-[state=active]:bg-purple-700 data-[state=active]:text-white transition-all"
                >
                  Architecture
                </TabsTrigger>
              </TabsList>
            </Tabs>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-12">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-8">

          {/* Query Tab */}
          <TabsContent value="query" className="space-y-8 animate-fade-in">
            <Card className="max-w-5xl mx-auto shadow-2xl border-0 bg-gradient-to-br from-white to-gray-50 dark:from-gray-800 dark:to-gray-900 backdrop-blur-xl overflow-hidden">
              <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-br from-blue-400 to-purple-600 opacity-10 blur-3xl rounded-full"></div>
              <CardHeader className="relative">
                <div className="flex items-center gap-3 mb-2">
                  <Sparkles className="h-8 w-8 text-purple-500 animate-pulse" />
                  <CardTitle className="text-4xl font-black bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent" style={{fontFamily: 'Space Grotesk, sans-serif'}}>Ask About Any Drug Interaction</CardTitle>
                </div>
                <CardDescription className="text-lg text-gray-600 dark:text-gray-300" style={{fontFamily: 'Inter, sans-serif'}}>Get instant, evidence-based answers powered by advanced AI and medical databases</CardDescription>
              </CardHeader>
              <CardContent className="relative">
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div className="space-y-3">
                    <label className="text-base font-bold text-gray-900 dark:text-white flex items-center gap-2" style={{fontFamily: 'Inter, sans-serif'}}>
                      <Target className="h-5 w-5 text-purple-500" />
                      Your Question
                    </label>
                    <Input
                      data-testid="query-input"
                      placeholder="e.g., Can I take aspirin with blood pressure medication?"
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      className="h-16 text-lg border-2 border-gray-300 dark:border-gray-600 focus:border-purple-500 dark:focus:border-purple-400 rounded-xl shadow-lg"
                      style={{fontFamily: 'Inter, sans-serif'}}
                      disabled={loading}
                    />
                  </div>

                  {loading && (
                    <div className="space-y-4 p-6 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-gray-700 dark:to-gray-600 rounded-xl">
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-10 border-4 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
                        <div className="flex-1">
                          <p className="text-lg font-bold text-gray-900 dark:text-white">{loadingStage}</p>
                          <Progress value={progress} className="h-2 mt-2" />
                        </div>
                      </div>
                    </div>
                  )}

                  <Button 
                    data-testid="submit-query-btn"
                    type="submit" 
                    className="w-full h-16 text-xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 hover:from-blue-700 hover:via-purple-700 hover:to-pink-700 shadow-2xl hover:shadow-3xl transform hover:scale-105 transition-all duration-300"
                    disabled={loading}
                    style={{fontFamily: 'Space Grotesk, sans-serif'}}
                  >
                    {loading ? (
                      <>
                        <div className="h-6 w-6 border-3 border-white border-t-transparent rounded-full animate-spin mr-3"></div>
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <Zap className="h-6 w-6 mr-3" />
                        Get AI Analysis
                      </>
                    )}
                  </Button>
                </form>

                {/* Example Queries */}
                <div className="mt-8 p-6 bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 dark:from-indigo-900/30 dark:via-purple-900/30 dark:to-pink-900/30 rounded-2xl border-2 border-indigo-200 dark:border-indigo-700 shadow-xl">
                  <p className="text-base font-bold text-indigo-900 dark:text-indigo-300 mb-4 flex items-center gap-2" style={{fontFamily: 'Inter, sans-serif'}}>
                    <Sparkles className="h-5 w-5" />
                    Try These Example Questions:
                  </p>
                  <div className="space-y-3">
                    {[
                      {q: "What are the interactions between aspirin and warfarin?", risk: "HIGH"},
                      {q: "Can I take metformin with insulin?", risk: "MODERATE"},
                      {q: "Is grapefruit juice safe with statins?", risk: "HIGH"},
                      {q: "Can I take vitamin C with aspirin?", risk: "LOW"}
                    ].map((example, idx) => (
                      <button
                        key={idx}
                        onClick={() => setQuery(example.q)}
                        className="w-full text-left p-4 bg-white dark:bg-gray-800 rounded-xl hover:bg-gradient-to-r hover:from-indigo-100 hover:to-purple-100 dark:hover:from-indigo-900 dark:hover:to-purple-900 transition-all duration-300 border-2 border-transparent hover:border-indigo-300 dark:hover:border-indigo-600 shadow-md hover:shadow-xl transform hover:scale-105"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex items-start gap-3">
                            <span className="text-indigo-500 dark:text-indigo-400 mt-1 text-xl">💊</span>
                            <span className="text-gray-700 dark:text-gray-200 font-medium">{example.q}</span>
                          </div>
                          <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                            example.risk === 'HIGH' ? 'bg-red-500 text-white' :
                            example.risk === 'MODERATE' ? 'bg-yellow-500 text-white' :
                            'bg-green-500 text-white'
                          }`}>
                            {example.risk}
                          </span>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Stats Cards */}
            {stats && (
              <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-8">
                <Card className="shadow-2xl border-0 bg-gradient-to-br from-blue-500 to-purple-600 text-white hover:shadow-3xl transform hover:scale-105 transition-all duration-300">
                  <CardHeader className="pb-4">
                    <CardTitle className="text-xl font-bold flex items-center gap-3" style={{fontFamily: 'Space Grotesk, sans-serif'}}>
                      <Award className="h-7 w-7" />
                      Total Analyses Completed
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-6xl font-black mb-2" data-testid="total-queries">{stats.total_queries}</p>
                    <p className="text-sm opacity-90">Powered by Advanced AI + DrugBank</p>
                  </CardContent>
                </Card>
                <Card className="shadow-2xl border-0 bg-gradient-to-br from-pink-500 to-red-600 text-white hover:shadow-3xl transform hover:scale-105 transition-all duration-300">
                  <CardHeader className="pb-4">
                    <CardTitle className="text-xl font-bold flex items-center gap-3" style={{fontFamily: 'Space Grotesk, sans-serif'}}>
                      <BarChart3 className="h-7 w-7" />
                      Risk Level Distribution
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {Object.entries(stats.risk_distribution || {}).map(([risk, count]) => (
                        <div key={risk} className="flex items-center justify-between p-3 bg-white/20 rounded-xl backdrop-blur-sm">
                          <div className="flex items-center gap-2">
                            {getRiskIcon(risk)}
                            <span className="font-bold text-lg">{risk}</span>
                          </div>
                          <span className="text-2xl font-black">{count}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
          </TabsContent>

          {/* Result Tab - Continue with enhanced styling... */}
          <TabsContent value="result" className="space-y-8 animate-fade-in">
            {result ? (
              <div className="max-w-5xl mx-auto space-y-8" data-testid="result-container">
                {/* Action Buttons */}
                <div className="flex justify-end gap-4">
                  <Button
                    onClick={() => addToComparison(result)}
                    variant="outline"
                    className="border-2 border-purple-500 text-purple-600 hover:bg-purple-50 dark:hover:bg-purple-900 font-bold shadow-lg"
                    data-testid="add-to-compare-btn"
                  >
                    <Plus className="h-5 w-5 mr-2" />
                    Add to Compare
                  </Button>
                  <Button
                    onClick={exportToPDF}
                    className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 font-bold shadow-xl"
                    data-testid="export-pdf-btn"
                  >
                    <Download className="h-5 w-5 mr-2" />
                    Download Report
                  </Button>
                </div>

                {/* Risk Assessment Card */}
                <Card className="shadow-2xl border-0 bg-gradient-to-br from-white to-gray-50 dark:from-gray-800 dark:to-gray-900">
                  <CardContent className="pt-8">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                      <div>
                        <p className="text-sm text-gray-500 dark:text-gray-400 mb-3 font-semibold">RISK ASSESSMENT</p>
                        <div className="flex items-center gap-4">
                          <div className={`p-5 rounded-2xl ${getRiskColor(result.risk_score)} shadow-2xl transform hover:scale-110 transition-all`}>
                            {getRiskIcon(result.risk_score)}
                          </div>
                          <div>
                            <span className="text-5xl font-black text-gray-900 dark:text-white" style={{fontFamily: 'Space Grotesk, sans-serif'}} data-testid="risk-score">{result.risk_score}</span>
                            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{getRiskDescription(result.risk_score)}</p>
                          </div>
                        </div>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500 dark:text-gray-400 mb-3 font-semibold">CONFIDENCE SCORE</p>
                        <div className="space-y-3">
                          <div className="flex items-end gap-3">
                            <p className="text-5xl font-black bg-gradient-to-r from-teal-600 to-emerald-600 bg-clip-text text-transparent" data-testid="grounding-score">{(result.grounding_score * 100).toFixed(0)}%</p>
                            <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">Based on {result.num_retrieved_docs} medical sources</p>
                          </div>
                          <Progress value={result.grounding_score * 100} className="h-3" />
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Your Question */}
                <Card className="shadow-2xl border-0 bg-white dark:bg-gray-800">
                  <CardHeader>
                    <CardTitle className="text-2xl font-bold flex items-center gap-3 dark:text-white" style={{fontFamily: 'Space Grotesk, sans-serif'}}>
                      <Target className="h-7 w-7 text-blue-500" />
                      Your Question
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-xl text-gray-700 dark:text-gray-200 font-medium leading-relaxed" style={{fontFamily: 'Inter, sans-serif'}} data-testid="query-text">{result.query}</p>
                  </CardContent>
                </Card>

                {/* AI Analysis */}
                <Card className="shadow-2xl border-0 bg-gradient-to-br from-blue-50 to-purple-50 dark:from-gray-800 dark:to-gray-900">
                  <CardHeader>
                    <CardTitle className="text-2xl font-bold flex items-center gap-3 dark:text-white" style={{fontFamily: 'Space Grotesk, sans-serif'}}>
                      <Brain className="h-7 w-7 text-purple-500" />
                      AI Analysis & Recommendations
                    </CardTitle>
                    <CardDescription className="text-base dark:text-gray-300">Generated by Gemini 2.5 Pro with verified medical sources</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="prose prose-lg max-w-none dark:prose-invert bg-white dark:bg-gray-800 p-6 rounded-xl shadow-inner">
                      <div className="whitespace-pre-wrap text-gray-800 dark:text-gray-200 leading-relaxed" style={{fontFamily: 'Inter, sans-serif'}} data-testid="response-text">{result.response}</div>
                    </div>
                  </CardContent>
                </Card>

                {/* Citations */}
                {result.citations && result.citations.length > 0 && (
                  <Card className="shadow-2xl border-0 bg-white dark:bg-gray-800">
                    <CardHeader>
                      <CardTitle className="text-2xl font-bold flex items-center gap-3 dark:text-white" style={{fontFamily: 'Space Grotesk, sans-serif'}}>
                        <Database className="h-7 w-7 text-emerald-500" />
                        Medical Sources & Evidence
                      </CardTitle>
                      <CardDescription className="text-base dark:text-gray-300" style={{fontFamily: 'Inter, sans-serif'}}>All information verified against DrugBank professional database</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <Accordion type="single" collapsible className="space-y-3">
                        {result.citations.map((citation, idx) => (
                          <AccordionItem key={idx} value={`citation-${idx}`} data-testid={`citation-item-${idx}`} className="border-2 border-gray-200 dark:border-gray-700 rounded-xl px-6 bg-gradient-to-r from-gray-50 to-white dark:from-gray-700 dark:to-gray-800 hover:border-emerald-300 dark:hover:border-emerald-600 transition-all">
                            <AccordionTrigger className="text-base hover:no-underline dark:text-gray-200 font-semibold" style={{fontFamily: 'Inter, sans-serif'}}>
                              <div className="flex items-center gap-4 flex-1">
                                <Badge variant="outline" className="bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-300 font-bold px-3 py-1">Source {idx + 1}</Badge>
                                <span className="text-left flex-1 font-bold">{citation.drug_name}</span>
                                <Badge className="bg-gradient-to-r from-teal-500 to-emerald-500 text-white font-bold">
                                  {(citation.relevance_score * 100).toFixed(0)}% Match
                                </Badge>
                              </div>
                            </AccordionTrigger>
                            <AccordionContent className="text-base text-gray-600 dark:text-gray-400 pt-4" style={{fontFamily: 'Inter, sans-serif'}}>
                              <div className="space-y-3 bg-gray-100 dark:bg-gray-700 p-6 rounded-xl">
                                <div className="flex items-center gap-2">
                                  <Database className="h-5 w-5 text-emerald-500" />
                                  <p><strong className="dark:text-gray-200">Database:</strong> {citation.source}</p>
                                </div>
                                <div className="flex items-center gap-2">
                                  <Award className="h-5 w-5 text-blue-500" />
                                  <p><strong className="dark:text-gray-200">Relevance:</strong> {(citation.relevance_score * 100).toFixed(1)}%</p>
                                </div>
                              </div>
                            </AccordionContent>
                          </AccordionItem>
                        ))}
                      </Accordion>
                    </CardContent>
                  </Card>
                )}
              </div>
            ) : (
              <Card className="max-w-5xl mx-auto shadow-2xl border-0 bg-gradient-to-br from-white to-gray-50 dark:from-gray-800 dark:to-gray-900">
                <CardContent className="py-24 text-center">
                  <Search className="h-24 w-24 text-gray-300 dark:text-gray-600 mx-auto mb-6" />
                  <p className="text-2xl text-gray-500 dark:text-gray-400 font-bold mb-2" style={{fontFamily: 'Inter, sans-serif'}}>No Results Yet</p>
                  <p className="text-gray-400 dark:text-gray-500">Submit a question to see your AI-powered analysis</p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* History Tab */}
          <TabsContent value="history" className="space-y-6 animate-fade-in">
            <Card className="max-w-5xl mx-auto shadow-2xl border-0 bg-white dark:bg-gray-800">
              <CardHeader>
                <CardTitle className="text-3xl font-bold flex items-center gap-3 dark:text-white" style={{fontFamily: 'Space Grotesk, sans-serif'}}>
                  <Clock className="h-8 w-8 text-pink-500" />
                  Your Analysis History
                </CardTitle>
                <CardDescription className="text-lg dark:text-gray-300" style={{fontFamily: 'Inter, sans-serif'}}>Review your previous drug interaction queries</CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[700px] pr-4">
                  {history.length > 0 ? (
                    <div className="space-y-4">
                      {history.map((item, idx) => (
                        <Card key={idx} className="border-2 shadow-lg hover:shadow-2xl transition-all dark:bg-gray-700 dark:border-gray-600 transform hover:scale-105" data-testid={`history-item-${idx}`}>
                          <CardContent className="pt-6">
                            <div className="space-y-4">
                              <div className="flex items-center justify-between">
                                <Badge className={`${getRiskColor(item.risk_score)} px-4 py-2 text-base font-bold`}>
                                  {getRiskIcon(item.risk_score)}
                                  <span className="ml-2">{item.risk_score}</span>
                                </Badge>
                                <div className="flex items-center gap-3">
                                  <span className="text-sm text-gray-500 dark:text-gray-400 font-medium" style={{fontFamily: 'Inter, sans-serif'}}>
                                    {new Date(item.timestamp).toLocaleString()}
                                  </span>
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => addToComparison(item)}
                                    className="border-2 border-purple-400 hover:bg-purple-50 dark:hover:bg-purple-900"
                                  >
                                    <Plus className="h-4 w-4 mr-1" />
                                    Compare
                                  </Button>
                                </div>
                              </div>
                              <p className="text-lg font-bold text-gray-900 dark:text-gray-100" style={{fontFamily: 'Inter, sans-serif'}}>{item.query}</p>
                              <p className="text-base text-gray-600 dark:text-gray-400 line-clamp-2" style={{fontFamily: 'Inter, sans-serif'}}>{item.response}</p>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-24">
                      <Clock className="h-24 w-24 text-gray-300 dark:text-gray-600 mx-auto mb-6" />
                      <p className="text-2xl text-gray-500 dark:text-gray-400 font-bold" style={{fontFamily: 'Inter, sans-serif'}}>No History Yet</p>
                    </div>
                  )}
                </ScrollArea>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Compare Tab */}
          <TabsContent value="compare" className="space-y-6 animate-fade-in">
            <Card className="max-w-6xl mx-auto shadow-2xl border-0 bg-white dark:bg-gray-800">
              <CardHeader>
                <CardTitle className="text-3xl font-bold flex items-center gap-3 dark:text-white" style={{fontFamily: 'Space Grotesk, sans-serif'}}>
                  <BarChart3 className="h-8 w-8 text-green-500" />
                  Side-by-Side Comparison
                </CardTitle>
                <CardDescription className="text-lg dark:text-gray-300" style={{fontFamily: 'Inter, sans-serif'}}>Compare up to 3 analyses to see differences</CardDescription>
              </CardHeader>
              <CardContent>
                {compareQueries.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {compareQueries.map((item, idx) => (
                      <Card key={idx} className="border-4 border-gray-300 dark:border-gray-600 dark:bg-gray-700 shadow-xl" data-testid={`compare-item-${idx}`}>
                        <CardHeader className="pb-4">
                          <div className="flex items-start justify-between">
                            <Badge className={`${getRiskColor(item.risk_score)} px-3 py-1 font-bold`}>{item.risk_score}</Badge>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => removeFromComparison(item.id)}
                              className="h-8 w-8 p-0 hover:bg-red-100 dark:hover:bg-red-900"
                            >
                              <X className="h-5 w-5 text-red-500" />
                            </Button>
                          </div>
                        </CardHeader>
                        <CardContent className="space-y-4">
                          <div>
                            <p className="text-xs text-gray-500 dark:text-gray-400 mb-2 font-semibold">Question:</p>
                            <p className="text-sm font-bold dark:text-gray-100" style={{fontFamily: 'Inter, sans-serif'}}>{item.query}</p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-500 dark:text-gray-400 mb-2 font-semibold">Confidence:</p>
                            <div className="flex items-center gap-3">
                              <Progress value={(item.grounding_score || 0) * 100} className="flex-1 h-3" />
                              <span className="text-sm font-bold dark:text-gray-200">{((item.grounding_score || 0) * 100).toFixed(0)}%</span>
                            </div>
                          </div>
                          <div>
                            <p className="text-xs text-gray-500 dark:text-gray-400 mb-2 font-semibold">Analysis:</p>
                            <p className="text-xs text-gray-600 dark:text-gray-400 line-clamp-6" style={{fontFamily: 'Inter, sans-serif'}}>{item.response}</p>
                          </div>
                          <div className="pt-3 border-t border-gray-200 dark:border-gray-600">
                            <p className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-2">
                              <Database className="h-4 w-4" />
                              {item.citations?.length || 0} Sources Cited
                            </p>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-24">
                    <BarChart3 className="h-24 w-24 text-gray-300 dark:text-gray-600 mx-auto mb-6" />
                    <p className="text-2xl text-gray-500 dark:text-gray-400 font-bold mb-3" style={{fontFamily: 'Inter, sans-serif'}}>No Comparisons Yet</p>
                    <p className="text-gray-400 dark:text-gray-500">Add queries from your History to compare them side-by-side</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Evaluation Tab */}
          <TabsContent value="evaluation" className="space-y-6 animate-fade-in">
            <EvaluationTab />
          </TabsContent>

          {/* System Architecture Tab */}
          <TabsContent value="architecture" className="space-y-6 animate-fade-in">
            <SystemArchitecture />
          </TabsContent>
        </Tabs>
      </main>

      {/* Beautiful Footer */}
      <footer className="border-t bg-gradient-to-r from-blue-900 via-purple-900 to-pink-900 text-white mt-20">
        <div className="container mx-auto px-4 py-12">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Column 1: About */}
            <div className="text-justify">
              <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                <Award className="h-5 w-5" />
                About MediSafe AI
              </h3>
              <p className="text-sm opacity-90 leading-relaxed">
                Graduate research project combining cutting-edge deep learning, graph networks, and medical databases for safer healthcare.
              </p>
            </div>

            {/* Column 2: Disclaimer */}
            <div className="text-justify">
              <h3 className="text-lg font-bold mb-4">⚠️ Medical Disclaimer</h3>
              <p className="text-sm opacity-90 leading-relaxed">
                This is an academic research system for educational purposes only. Information provided should NOT replace professional medical advice. Always consult qualified healthcare professionals before making medication decisions.
              </p>
            </div>

            {/* Column 3: Team */}
            <div className="text-justify">
              <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                <Brain className="h-5 w-5" />
                TEAM
              </h3>
              <div className="space-y-2 text-sm opacity-90">
                <p className="font-semibold">Maahi Patel</p>
                <p className="font-semibold">Jinay Shah</p>
                <p className="font-semibold">Prakhar Pandey</p>
              </div>
              <div className="mt-4 pt-4 border-t border-white/20">
                <p className="text-sm opacity-75">Rice University</p>
                <p className="text-sm opacity-75">MS Computer Science</p>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
