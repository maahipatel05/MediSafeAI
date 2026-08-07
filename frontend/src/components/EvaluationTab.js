import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { AlertCircle, BarChart3, TrendingUp, Award, Target, Brain } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from './ui/alert';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

const COLORS = ['#3b82f6', '#8b5cf6', '#ec4899', '#10b981', '#f59e0b', '#ef4444'];

// Real numbers from backend/results/*.json and backend/run_retrieval_evaluation.py,
// run against the same 8-query ground-truth set (evaluation.py). Reflects the
// latest checked-in evaluation run, not a live fetch -- there is no backend
// endpoint serving this yet.
const EVALUATION_DATA = {
  rerankingImpact: {
    before: { 'precision@5': 0.525, 'recall@5': 0.7396, 'ndcg@5': 0.7364, mrr: 0.7083 },
    after: { 'precision@5': 0.775, 'recall@5': 0.875, 'ndcg@5': 0.8451, mrr: 0.8125 }
  },
  backendComparison: {
    faiss: { 'precision@5': 0.525, 'recall@5': 0.7396, 'ndcg@5': 0.7364, mrr: 0.7083 },
    azure: { 'precision@5': 0.525, 'recall@5': 0.7396, 'ndcg@5': 0.7364, mrr: 0.7083 }
  },
  endToEnd: {
    groundingScore: 0.815,
    semanticGrounding: 0.922,
    overallConfidence: 0.869,
    hallucinationRate: 0.0,
    avgLatencySeconds: 5.78
  },
  dataset: {
    primaryDrugs: 500,
    uniqueDrugNames: 2188,
    totalChunks: 11798,
    interactionRecords: 11192
  }
};

const EvaluationTab = () => {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Static real results -- no live fetch yet, see comment above EVALUATION_DATA.
    const t = setTimeout(() => setLoading(false), 300);
    return () => clearTimeout(t);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-300">Loading evaluation results...</p>
        </div>
      </div>
    );
  }

  const { rerankingImpact, backendComparison, endToEnd, dataset } = EVALUATION_DATA;

  const rerankingData = [
    { metric: 'Precision@5', Before: pct(rerankingImpact.before['precision@5']), After: pct(rerankingImpact.after['precision@5']) },
    { metric: 'Recall@5', Before: pct(rerankingImpact.before['recall@5']), After: pct(rerankingImpact.after['recall@5']) },
    { metric: 'NDCG@5', Before: pct(rerankingImpact.before['ndcg@5']), After: pct(rerankingImpact.after['ndcg@5']) },
    { metric: 'MRR', Before: pct(rerankingImpact.before.mrr), After: pct(rerankingImpact.after.mrr) }
  ];

  const backendData = [
    { metric: 'Precision@5', FAISS: pct(backendComparison.faiss['precision@5']), Azure: pct(backendComparison.azure['precision@5']) },
    { metric: 'Recall@5', FAISS: pct(backendComparison.faiss['recall@5']), Azure: pct(backendComparison.azure['recall@5']) },
    { metric: 'NDCG@5', FAISS: pct(backendComparison.faiss['ndcg@5']), Azure: pct(backendComparison.azure['ndcg@5']) },
    { metric: 'MRR', FAISS: pct(backendComparison.faiss.mrr), Azure: pct(backendComparison.azure.mrr) }
  ];

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="text-center space-y-4">
        <div className="flex items-center justify-center gap-3">
          <Award className="h-12 w-12 text-blue-500" />
          <h2 className="text-5xl font-bold gradient-text">
            Performance Evaluation
          </h2>
        </div>
        <p className="text-xl text-gray-300 max-w-4xl mx-auto">
          Real results from the evaluation scripts checked into this repo (backend/results/, backend/run_retrieval_evaluation.py),
          run on an 8-query ground-truth set against a {dataset.primaryDrugs}-drug DrugBank corpus.
        </p>
      </div>

      {/* Reranking Impact */}
      <Card className="max-w-6xl mx-auto shadow-xl">
        <CardHeader>
          <CardTitle className="text-2xl flex items-center gap-3">
            <Brain className="h-7 w-7 text-blue-600" />
            Cross-Encoder Reranking Impact
          </CardTitle>
          <CardDescription>Bi-encoder top-5 vs. bi-encoder top-20 re-ranked to top-5 by a cross-encoder</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={rerankingData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="metric" stroke="#6b7280" />
              <YAxis stroke="#6b7280" label={{ value: 'Score (%)', angle: -90, position: 'insideLeft' }} domain={[0, 100]} />
              <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px', color: '#fff' }} />
              <Legend />
              <Bar dataKey="Before" fill="#94a3b8" radius={[8, 8, 0, 0]} />
              <Bar dataKey="After" fill="#3b82f6" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
          <div className="mt-6 bg-blue-900/20 border border-blue-500/30 p-4 rounded-lg">
            <div className="text-sm text-gray-300">
              Reranking (bi-encoder top-20 &rarr; cross-encoder top-5) lifted precision@5 from{' '}
              <strong>52.5% to 77.5%</strong> on this ground-truth set -- the largest gain of any metric measured.
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Backend Comparison */}
      <Card className="max-w-6xl mx-auto shadow-xl">
        <CardHeader>
          <CardTitle className="text-2xl flex items-center gap-3">
            <BarChart3 className="h-7 w-7 text-purple-600" />
            FAISS vs. Azure AI Search
          </CardTitle>
          <CardDescription>Same embedding model, same document set, same queries -- only the vector backend differs</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={backendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="metric" stroke="#6b7280" />
              <YAxis stroke="#6b7280" label={{ value: 'Score (%)', angle: -90, position: 'insideLeft' }} domain={[0, 100]} />
              <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px', color: '#fff' }} />
              <Legend />
              <Bar dataKey="FAISS" fill="#10b981" radius={[8, 8, 0, 0]} />
              <Bar dataKey="Azure" fill="#f59e0b" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
          <div className="mt-6 bg-purple-900/20 border border-purple-500/30 p-4 rounded-lg">
            <div className="text-sm text-gray-300">
              Identical, verified document-for-document -- Azure's approximate HNSW index found the same top-5
              results as FAISS's exact search on every query in this evaluation set.
            </div>
          </div>
        </CardContent>
      </Card>

      {/* End-to-end pipeline */}
      <Card className="max-w-6xl mx-auto shadow-xl">
        <CardHeader>
          <CardTitle className="text-2xl flex items-center gap-3">
            <Target className="h-7 w-7 text-pink-600" />
            End-to-End Pipeline (Retrieval + Reranking + Generation)
          </CardTitle>
          <CardDescription>Full 3-agent LangGraph pipeline, CPU-only local inference</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatTile label="Grounding Score" value={`${pct(endToEnd.groundingScore)}%`} />
            <StatTile label="Confidence" value={`${pct(endToEnd.overallConfidence)}%`} />
            <StatTile label="Avg Latency" value={`${endToEnd.avgLatencySeconds}s`} />
            <StatTile label="Hallucination Rate" value={`${pct(endToEnd.hallucinationRate)}%`} />
          </div>
          <div className="mt-6 bg-pink-900/20 border border-pink-500/30 p-4 rounded-lg">
            <div className="text-sm text-gray-300 space-y-2">
              <p>
                Confidence is a semantic-similarity check (same MiniLM encoder used for retrieval) between each
                generated sentence and its retrieved evidence -- not a trained hallucination classifier.
              </p>
              <p>
                The 0% hallucination rate reflects a <strong>confidence-gated extractive fallback</strong>: when the
                local FLAN-T5 model's own paraphrase doesn't clear the grounding threshold, it's replaced with a
                verbatim quote from the retrieved source instead of an unverified paraphrase. On this evaluation
                set the fallback triggered on all 8/8 queries -- this measures what the system shows the user, not
                that the underlying model never confabulates on its own.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Dataset */}
      <Card className="max-w-6xl mx-auto shadow-xl">
        <CardHeader>
          <CardTitle className="text-2xl flex items-center gap-3">
            <TrendingUp className="h-7 w-7 text-green-600" />
            Dataset
          </CardTitle>
          <CardDescription>Parsed from the DrugBank Open Access dataset (not redistributed in this repo)</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatTile label="Primary Drugs Parsed" value={dataset.primaryDrugs.toLocaleString()} />
            <StatTile label="Unique Drug Names" value={dataset.uniqueDrugNames.toLocaleString()} />
            <StatTile label="Total Chunks" value={dataset.totalChunks.toLocaleString()} />
            <StatTile label="Interaction Records" value={dataset.interactionRecords.toLocaleString()} />
          </div>
        </CardContent>
      </Card>

      <Alert className="max-w-6xl mx-auto">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Small evaluation set</AlertTitle>
        <AlertDescription>
          These numbers come from an 8-query hand-written ground-truth set, not a large standardized benchmark --
          treat them as a real, reproducible smoke test of the pipeline rather than a statistically powered result.
        </AlertDescription>
      </Alert>
    </div>
  );
};

const StatTile = ({ label, value }) => (
  <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow text-center">
    <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">{value}</div>
    <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">{label}</div>
  </div>
);

function pct(fraction) {
  return parseFloat((fraction * 100).toFixed(1));
}

export default EvaluationTab;
