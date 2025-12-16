import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Brain, Database, Zap, Shield, Network, Cpu, GitBranch, Layers, Box } from 'lucide-react';

const SystemArchitecture = () => {
  const architectureSections = [
    {
      title: "System Overview",
      icon: <Layers className="h-6 w-6" />,
      color: "from-blue-500 to-cyan-500",
      content: {
        description: "MediSafe AI is a production-grade Grounded Agentic RAG (Retrieval-Augmented Generation) system designed for drug interaction analysis and safety assessment.",
        keyPoints: [
          "Multi-agent architecture with specialized components",
          "DrugBank database with 12,000+ pharmaceutical entries",
          "Real-time AI-powered analysis using Local FLAN-T5",
          "FAISS vector search for semantic retrieval"
        ]
      }
    },
    {
      title: "1. Query Decomposition Agent",
      icon: <GitBranch className="h-6 w-6" />,
      color: "from-purple-500 to-indigo-500",
      content: {
        description: "Breaks down complex medical queries into simpler, focused sub-queries for more accurate retrieval.",
        workflow: [
          "User submits complex query (e.g., 'Can I take aspirin with warfarin while on blood pressure medication?')",
          "Agent analyzes query structure and medical context",
          "Decomposes into 2-4 focused sub-queries",
          "Each sub-query targets specific aspects (drug A effects, drug B effects, interaction mechanisms)"
        ],
        technical: {
          model: "Local FLAN-T5",
          method: "Prompt engineering with structured JSON output",
          averageTime: "~2-3 seconds"
        }
      }
    },
    {
      title: "2. Retrieval Agent (Semantic Search)",
      icon: <Database className="h-6 w-6" />,
      color: "from-cyan-500 to-blue-500",
      content: {
        description: "Uses FAISS vector search with sentence transformers to find relevant drug information from the DrugBank database.",
        workflow: [
          "Receives sub-queries from decomposition agent",
          "Converts queries to 384-dimensional embeddings using sentence-transformers",
          "Searches FAISS index containing 12,000+ drug embeddings",
          "Returns top-K most semantically similar documents",
          "Deduplicates and ranks results across all sub-queries"
        ],
        technical: {
          embeddingModel: "all-MiniLM-L6-v2 (sentence-transformers)",
          indexType: "FAISS IndexFlatIP (Inner Product)",
          retrievalK: "3-5 documents per sub-query",
          searchTime: "<100ms"
        }
      }
    },
    {
      title: "3. Cross-Encoder Re-Ranking",
      icon: <Shield className="h-6 w-6" />,
      color: "from-indigo-500 to-purple-500",
      content: {
        description: "Improves retrieval accuracy by re-scoring initial results with a more powerful cross-encoder model.",
        workflow: [
          "Takes initial retrieval results from bi-encoder",
          "Creates (query, document) pairs",
          "Scores each pair with cross-encoder",
          "Re-ranks documents by new scores",
          "Returns refined top-K results"
        ],
        technical: {
          model: "ms-marco-MiniLM-L-6-v2",
          architecture: "Cross-encoder (joint query-document encoding)",
          improvement: "~15-20% precision gain over bi-encoder alone"
        }
      }
    },
    {
      title: "4. Generation Agent (Response Synthesis)",
      icon: <Brain className="h-6 w-6" />,
      color: "from-blue-500 to-purple-500",
      content: {
        description: "Generates grounded, evidence-based responses with proper citations and risk assessment.",
        workflow: [
          "Receives top-ranked documents from retrieval",
          "Constructs context from drug information and interactions",
          "Generates comprehensive response with Local FLAN-T5",
          "Enforces strict grounding to provided sources",
          "Extracts risk score (LOW/MODERATE/HIGH/CRITICAL)",
          "Creates citations linking claims to sources"
        ],
        technical: {
          model: "Local FLAN-T5",
          temperature: "0.7 for balanced creativity/accuracy",
          maxTokens: "2048",
          groundingMethod: "Prompt engineering with source attribution"
        }
      }
    },
    {
      title: "5. Drug Interaction Graph",
      icon: <Network className="h-6 w-6" />,
      color: "from-green-500 to-emerald-500",
      content: {
        description: "Novel graph-based architecture representing drugs as nodes and interactions as weighted edges.",
        features: [
          "Drugs represented as nodes in NetworkX graph",
          "Interactions as edges with severity weights (1-4)",
          "Graph-enhanced retrieval using neighbor expansion",
          "Centrality analysis to identify high-risk drugs",
          "Community detection for drug cluster identification"
        ],
        technical: {
          library: "NetworkX 3.5",
          nodeCount: "~8,000 unique drugs",
          edgeCount: "~15,000 documented interactions",
          algorithms: ["Betweenness centrality", "Community detection", "Shortest path"]
        }
      }
    },
    {
      title: "6. Uncertainty Quantification",
      icon: <Zap className="h-6 w-6" />,
      color: "from-yellow-500 to-orange-500",
      content: {
        description: "Provides confidence scores and detects potential hallucinations in generated responses.",
        components: [
          "Monte Carlo Dropout: Generates multiple predictions to estimate uncertainty",
          "Retrieval Confidence: Analyzes score variance and coverage",
          "Grounding Verification: Checks if claims are supported by sources",
          "Hallucination Detection: Identifies unsupported statements",
          "Overall Confidence Scoring: Weighted combination of all signals"
        ],
        technical: {
          samplingMethod: "Multiple generation passes (3-5 samples)",
          claimExtraction: "Sentence-based factual statement parsing",
          verificationThreshold: "50% word overlap with sources"
        }
      }
    },
    {
      title: "Data Flow & Processing Pipeline",
      icon: <Box className="h-6 w-6" />,
      color: "from-pink-500 to-rose-500",
      content: {
        description: "Complete end-to-end processing pipeline from user query to final response.",
        steps: [
          "1. User Query → Query Decomposition Agent (2-3s)",
          "2. Sub-queries → Retrieval Agent (FAISS search <100ms)",
          "3. Initial Results → Cross-Encoder Re-Ranking (~500ms)",
          "4. Ranked Documents + Query → Generation Agent (8-12s)",
          "5. Response → Grounding Verification (1-2s)",
          "6. Final Response + Metadata → User Interface"
        ],
        totalTime: "~12-18 seconds per query",
        caching: "MongoDB stores all query history for reuse"
      }
    },
    {
      title: "Technology Stack",
      icon: <Cpu className="h-6 w-6" />,
      color: "from-red-500 to-orange-500",
      content: {
        frontend: [
          "React 19 with Hooks",
          "Tailwind CSS for styling",
          "Shadcn UI components",
          "Recharts for visualizations",
          "Axios for API communication"
        ],
        backend: [
          "FastAPI (Python async web framework)",
          "Motor (Async MongoDB driver)",
          "Uvicorn (ASGI server)",
          "Sentence Transformers",
          "FAISS (Facebook AI Similarity Search)"
        ],
        aiModels: [
          "Local FLAN-T5 (Google)",
          "all-MiniLM-L6-v2 (Bi-encoder)",
          "ms-marco-MiniLM-L-6-v2 (Cross-encoder)"
        ],
        database: [
          "MongoDB (query history)",
          "DrugBank XML (drug data)",
          "FAISS index (vector embeddings)"
        ]
      }
    }
  ];

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="text-center space-y-4">
        <div className="flex items-center justify-center gap-3">
          <Layers className="h-12 w-12 text-blue-500" />
          <h2 className="text-4xl md:text-5xl font-bold gradient-text">
            System Architecture
          </h2>
        </div>
        <p className="text-lg text-gray-400 max-w-4xl mx-auto">
          Comprehensive technical documentation of the MediSafe AI system architecture, components, and data flow
        </p>
      </div>

      {/* Architecture Sections */}
      {architectureSections.map((section, index) => (
        <Card key={index} className="bg-gray-900 border-gray-800">
          <CardHeader>
            <CardTitle className="text-2xl flex items-center gap-3">
              <div className={`p-2 rounded-lg bg-gradient-to-br ${section.color}`}>
                {section.icon}
              </div>
              {section.title}
            </CardTitle>
            {section.content.description && (
              <CardDescription className="text-base text-gray-300 mt-2">
                {section.content.description}
              </CardDescription>
            )}
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Key Points */}
            {section.content.keyPoints && (
              <div className="space-y-2">
                <h4 className="font-semibold text-blue-400">Key Features:</h4>
                <ul className="space-y-1 ml-4">
                  {section.content.keyPoints.map((point, i) => (
                    <li key={i} className="text-gray-300 flex items-start gap-2">
                      <span className="text-blue-500 mt-1">•</span>
                      <span>{point}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Workflow */}
            {section.content.workflow && (
              <div className="space-y-2">
                <h4 className="font-semibold text-purple-400">Processing Workflow:</h4>
                <ol className="space-y-2 ml-4">
                  {section.content.workflow.map((step, i) => (
                    <li key={i} className="text-gray-300 flex items-start gap-3">
                      <span className="bg-purple-500/20 text-purple-300 px-2 py-0.5 rounded text-sm font-semibold">
                        {i + 1}
                      </span>
                      <span className="flex-1">{step}</span>
                    </li>
                  ))}
                </ol>
              </div>
            )}

            {/* Features */}
            {section.content.features && (
              <div className="space-y-2">
                <h4 className="font-semibold text-green-400">Features:</h4>
                <ul className="space-y-1 ml-4">
                  {section.content.features.map((feature, i) => (
                    <li key={i} className="text-gray-300 flex items-start gap-2">
                      <span className="text-green-500 mt-1">✓</span>
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Components */}
            {section.content.components && (
              <div className="space-y-2">
                <h4 className="font-semibold text-yellow-400">Components:</h4>
                <ul className="space-y-1 ml-4">
                  {section.content.components.map((comp, i) => (
                    <li key={i} className="text-gray-300 flex items-start gap-2">
                      <span className="text-yellow-500 mt-1">◆</span>
                      <span>{comp}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Steps */}
            {section.content.steps && (
              <div className="space-y-2">
                <h4 className="font-semibold text-pink-400">Processing Steps:</h4>
                <div className="space-y-2 ml-4">
                  {section.content.steps.map((step, i) => (
                    <div key={i} className="text-gray-300 bg-gray-800/50 p-3 rounded-lg">
                      {step}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Technical Details */}
            {section.content.technical && (
              <div className="bg-gray-800/50 p-4 rounded-lg space-y-2">
                <h4 className="font-semibold text-cyan-400 mb-3">Technical Specifications:</h4>
                {Object.entries(section.content.technical).map(([key, value]) => (
                  <div key={key} className="flex items-start gap-3">
                    <span className="font-mono text-sm text-cyan-300 min-w-[140px]">{key}:</span>
                    <span className="text-gray-300 text-sm">{value}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Stack Lists */}
            {section.content.frontend && (
              <div className="grid md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <h4 className="font-semibold text-blue-400">Frontend:</h4>
                  <ul className="space-y-1 text-sm text-gray-300">
                    {section.content.frontend.map((item, i) => (
                      <li key={i} className="flex items-center gap-2">
                        <span className="text-blue-500">▸</span> {item}
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="space-y-2">
                  <h4 className="font-semibold text-purple-400">Backend:</h4>
                  <ul className="space-y-1 text-sm text-gray-300">
                    {section.content.backend.map((item, i) => (
                      <li key={i} className="flex items-center gap-2">
                        <span className="text-purple-500">▸</span> {item}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {section.content.aiModels && (
              <div className="grid md:grid-cols-2 gap-4 mt-4">
                <div className="space-y-2">
                  <h4 className="font-semibold text-green-400">AI Models:</h4>
                  <ul className="space-y-1 text-sm text-gray-300">
                    {section.content.aiModels.map((item, i) => (
                      <li key={i} className="flex items-center gap-2">
                        <span className="text-green-500">▸</span> {item}
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="space-y-2">
                  <h4 className="font-semibold text-yellow-400">Database:</h4>
                  <ul className="space-y-1 text-sm text-gray-300">
                    {section.content.database.map((item, i) => (
                      <li key={i} className="flex items-center gap-2">
                        <span className="text-yellow-500">▸</span> {item}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {/* Additional Info */}
            {section.content.totalTime && (
              <div className="bg-blue-500/10 border border-blue-500/30 p-3 rounded-lg">
                <div className="flex items-center gap-2 text-blue-300">
                  <Zap className="h-5 w-5" />
                  <span className="font-semibold">Performance:</span>
                  <span>{section.content.totalTime}</span>
                </div>
                {section.content.caching && (
                  <div className="text-sm text-gray-400 mt-1 ml-7">
                    {section.content.caching}
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      ))}

      {/* System Diagram Summary */}
      <Card className="bg-gradient-to-br from-gray-900 to-gray-800 border-gray-700">
        <CardHeader>
          <CardTitle className="text-2xl gradient-text">Complete System Flow</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="bg-gray-800/50 p-6 rounded-lg font-mono text-sm text-gray-300 space-y-2">
            <div>┌─ User Query</div>
            <div>│</div>
            <div>├─▶ [1] Query Decomposition Agent (Local FLAN-T5)</div>
            <div>│   └─▶ Sub-queries: [Q1, Q2, Q3]</div>
            <div>│</div>
            <div>├─▶ [2] Retrieval Agent (FAISS + Sentence Transformers)</div>
            <div>│   └─▶ Initial Results: Top-20 documents</div>
            <div>│</div>
            <div>├─▶ [3] Cross-Encoder Re-Ranking (ms-marco)</div>
            <div>│   └─▶ Refined Results: Top-6 documents</div>
            <div>│</div>
            <div>├─▶ [4] Generation Agent (Local FLAN-T5)</div>
            <div>│   └─▶ Grounded Response + Citations + Risk Score</div>
            <div>│</div>
            <div>├─▶ [5] Uncertainty Quantification</div>
            <div>│   └─▶ Confidence Score + Hallucination Check</div>
            <div>│</div>
            <div>└─▶ Final Response → MongoDB → User Interface</div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default SystemArchitecture;