import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Brain, Database, Shield, Network, Cpu, GitBranch, Layers, Box } from 'lucide-react';

const SystemArchitecture = () => {
  const architectureSections = [
    {
      title: "System Overview",
      icon: <Layers className="h-6 w-6" />,
      color: "from-blue-500 to-cyan-500",
      content: {
        description: "MediSafe AI is a grounded, retrieval-augmented drug-interaction assistant. Every answer is backed by citations into a DrugBank-derived knowledge base.",
        keyPoints: [
          "Three-agent pipeline orchestrated via LangGraph",
          "500 primary DrugBank entries parsed, 2,188+ unique drug names referenced across interactions",
          "Swappable retrieval backend: FAISS (exact) or Azure AI Search (HNSW approximate)",
          "Local FLAN-T5 generation -- no external LLM API required"
        ]
      }
    },
    {
      title: "1. Query Agent",
      icon: <GitBranch className="h-6 w-6" />,
      color: "from-purple-500 to-indigo-500",
      content: {
        description: "Extracts a drug pair from the query and expands it with known synonyms and drug-class terms before retrieval.",
        workflow: [
          "User submits a query (e.g., 'Can I take ibuprofen with blood pressure medication?')",
          "Attempts to match two known drug names directly in the query text",
          "Expands generic terms (drug classes, brand names) into the specific ingredient names the corpus indexes on"
        ],
        technical: {
          module: "backend/local_llm_agent.py (QueryAgent)",
          drugMatching: "backend/drug_name_extractor.py",
          expansion: "backend/drug_knowledge.py (medication classes + synonyms)"
        }
      }
    },
    {
      title: "2. Retrieval Agent",
      icon: <Database className="h-6 w-6" />,
      color: "from-cyan-500 to-blue-500",
      content: {
        description: "Hybrid retrieval: a bi-encoder fetches broad candidates, then a cross-encoder re-ranks them for precision.",
        workflow: [
          "Bi-encoder (all-MiniLM-L6-v2) embeds the query and searches the vector index for the top 20 candidates",
          "Cross-encoder (ms-marco-MiniLM-L-6-v2) scores each (query, document) pair directly",
          "Re-ranks and returns the top 5 documents"
        ],
        technical: {
          embeddingModel: "all-MiniLM-L6-v2 (384-dim)",
          backend: "FAISS IndexFlatL2 (default) or Azure AI Search HNSW, via RETRIEVAL_BACKEND",
          rerankerModel: "cross-encoder/ms-marco-MiniLM-L-6-v2",
          measuredImpact: "precision@5 52.5% -> 77.5% from reranking (measured, 8-query eval set)"
        }
      }
    },
    {
      title: "3. Generation Agent",
      icon: <Brain className="h-6 w-6" />,
      color: "from-blue-500 to-purple-500",
      content: {
        description: "Generates a grounded explanation, assesses interaction risk, and gates the answer on a real confidence check.",
        workflow: [
          "FLAN-T5-large generates an answer from the top-5 retrieved documents",
          "The generated sentence is checked for semantic similarity against the retrieved evidence",
          "If it doesn't clear the grounding threshold, it's replaced with a verbatim quote from the source document instead (confidence-gated extractive fallback)",
          "Interaction severity is looked up in the drug interaction graph, falling back to an embedding-similarity ontology match if no graph edge exists",
          "Builds citations and a grounding score from the reranker's own relevance scores"
        ],
        technical: {
          model: "Local FLAN-T5-large (CPU)",
          confidenceCheck: "Cosine similarity vs. retrieved evidence, same MiniLM encoder used for retrieval",
          measuredResult: "0% hallucination rate on the 8-query eval set (fallback triggered 8/8)"
        }
      }
    },
    {
      title: "Drug Interaction Graph",
      icon: <Network className="h-6 w-6" />,
      color: "from-green-500 to-emerald-500",
      content: {
        description: "In-memory graph of drug-drug interactions, derived from the parsed DrugBank chunks, used for the preferred (fast) risk-severity lookup path.",
        features: [
          "Nodes are drug names; edges are interaction pairs with a classified severity",
          "Severity (S0-S3) classified via embedding similarity against a clinical-severity rubric, since DrugBank's raw interaction records carry no severity field",
          "Falls back to an ontology similarity match at query time when a pair has no graph edge"
        ],
        technical: {
          library: "Custom adjacency-map graph (backend/drug_graph.py)",
          interactionRecords: "11,192 pairwise records",
          uniqueDrugNames: "2,188 referenced across those records",
          severityBreakdown: "177 major, 1 moderate, 677 minor, 10,337 below confidence threshold"
        }
      }
    },
    {
      title: "Data Flow & Processing Pipeline",
      icon: <Box className="h-6 w-6" />,
      color: "from-pink-500 to-rose-500",
      content: {
        description: "End-to-end pipeline from user query to final response, orchestrated as an explicit LangGraph state machine.",
        steps: [
          "1. User Query -> Query Agent (drug-pair extraction + expansion)",
          "2. Expanded Query -> Retrieval Agent (bi-encoder top-20 -> cross-encoder top-5)",
          "3. Top-5 Documents -> Generation Agent (FLAN-T5 + confidence gate)",
          "4. Risk Assessment -> Graph lookup, or ontology fallback if no edge",
          "5. Final Response + Citations + Grounding Score -> MongoDB -> User Interface"
        ],
        totalTime: "~5.8s average end-to-end latency (measured, CPU-only local inference, 8-query eval set)",
        caching: "MongoDB stores query history for the History and Compare tabs"
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
          "LangGraph (agent orchestration)",
          "Motor (async MongoDB driver)",
          "Sentence Transformers",
          "FAISS / Azure AI Search (swappable retrieval backend)"
        ],
        aiModels: [
          "Local FLAN-T5-large (Google)",
          "all-MiniLM-L6-v2 (bi-encoder)",
          "ms-marco-MiniLM-L-6-v2 (cross-encoder)"
        ],
        database: [
          "MongoDB (query history)",
          "DrugBank-derived chunk data (checked into the repo)",
          "FAISS index / Azure AI Search index"
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
          Technical documentation of the MediSafe AI system architecture, components, and data flow
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
                  <Shield className="h-5 w-5" />
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
            <div>├─▶ [1] Query Agent (drug-pair extraction + expansion)</div>
            <div>│</div>
            <div>├─▶ [2] Retrieval Agent (bi-encoder top-20 → cross-encoder top-5)</div>
            <div>│   └─▶ FAISS or Azure AI Search, selected via RETRIEVAL_BACKEND</div>
            <div>│</div>
            <div>├─▶ [3] Generation Agent (Local FLAN-T5 + confidence gate)</div>
            <div>│   └─▶ Grounded Response + Citations + Risk Score</div>
            <div>│</div>
            <div>└─▶ Final Response → MongoDB → User Interface</div>
          </div>
          <div className="mt-4 text-sm text-gray-400">
            Orchestrated as a LangGraph state machine: expand → retrieve → generate → graph-risk lookup
            (falling back to an ontology similarity match when no graph edge exists) → compile.
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default SystemArchitecture;
