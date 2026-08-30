import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ShoppingCart, Play, CheckCircle, XCircle, Database, 
  Activity, ChevronDown, ChevronUp, RefreshCw, Sliders, 
  Search, ArrowRight, Clock, ShieldAlert, Sparkles, TrendingUp
} from 'lucide-react';


// Models matching our app/models.py
interface CartItem {
  id: string;
  price: number;
  category: string;
}

interface Cart {
  id: string;
  items: CartItem[];
  order_value: number;
  customer_id: string;
  has_active_discount: boolean;
  purchase_history: string[];
  declined_upsells_count: number;
  simulate_outcome: {
    accepted: boolean;
    order_value_delta: number;
  } | null;
}

interface ToolCall {
  id: string;
  tool_name: string;
  cart_id: string;
  payload: any;
  timestamp: string;
}

interface Decision {
  id: string;
  cart_id: string;
  decision_type: 'PROPOSE' | 'DECLINE';
  confidence_score: number;
  reason: string;
  rule_triggered: string | null;
  timestamp: string;
}

interface Outcome {
  id: string;
  decision_id: string;
  accepted: boolean | null;
  order_value_delta: number;
  timestamp: string;
}

interface AuditRecord {
  id: string;
  cart_id: string;
  tool_call: ToolCall | null;
  decision: Decision;
  outcome: Outcome | null;
  timestamp: string;
}

interface BatchResults {
  total_carts: number;
  total_propose: number;
  total_decline: number;
  decline_rate_pct: number;
  total_baseline_value: number;
  total_gained_upsell_value: number;
  uplift_percentage: number;
  decline_reasons_breakdown: {
    "No rules triggered": number;
    "Discount conflict": number;
    "Below confidence threshold": number;
  };
  confidence_score_distribution: {
    [key: string]: number;
  };
}

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

export default function App() {
  const [carts, setCarts] = useState<Cart[]>([]);
  const [selectedCart, setSelectedCart] = useState<Cart | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeFilter, setActiveFilter] = useState<'ALL' | 'ACTIVE_DISCOUNT' | 'PREVIOUS_DECLINES' | 'HIGH_VALUE'>('ALL');
  
  // Evaluation States
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [evaluationResult, setEvaluationResult] = useState<AuditRecord | null>(null);
  const [evalProgress, setEvalProgress] = useState<'idle' | 'fetching' | 'rules' | 'guardrails' | 'outcome' | 'saving' | 'done'>('idle');
  const [animatedConfidence, setAnimatedConfidence] = useState(0);

  // Batch / Audit logs states
  const [batchResults, setBatchResults] = useState<BatchResults | null>(null);
  const [auditRecords, setAuditRecords] = useState<AuditRecord[]>([]);
  const [expandedRecord, setExpandedRecord] = useState<string | null>(null);
  const [isRefreshingLogs, setIsRefreshingLogs] = useState(false);

  // Loading states
  const [isLoadingCarts, setIsLoadingCarts] = useState(true);
  const [isLoadingBatch, setIsLoadingBatch] = useState(true);

  // Fetch all basic data
  const fetchData = async () => {
    try {
      setIsLoadingCarts(true);
      const resCarts = await fetch(`${BACKEND_URL}/carts`);
      const cartsData = await resCarts.json();
      setCarts(cartsData);
      if (cartsData.length > 0) {
        setSelectedCart(cartsData[0]);
      }
    } catch (err) {
      console.error('Error fetching carts:', err);
    } finally {
      setIsLoadingCarts(false);
    }

    try {
      setIsLoadingBatch(true);
      const resBatch = await fetch(`${BACKEND_URL}/batch-results`);
      const batchData = await resBatch.json();
      if (!batchData.error) {
        setBatchResults(batchData);
      }
    } catch (err) {
      console.error('Error fetching batch results:', err);
    } finally {
      setIsLoadingBatch(false);
    }

    await refreshAuditRecords();
  };

  const refreshAuditRecords = async () => {
    setIsRefreshingLogs(true);
    try {
      const resAudit = await fetch(`${BACKEND_URL}/audit-records`);
      const auditData = await resAudit.json();
      // Sort descending (most recent first)
      const sortedAudit = Array.isArray(auditData) 
        ? auditData.sort((a, b) => parseFloat(b.timestamp) - parseFloat(a.timestamp))
        : [];
      setAuditRecords(sortedAudit);
    } catch (err) {
      console.error('Error fetching audit logs:', err);
    } finally {
      setIsRefreshingLogs(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Run a single cart evaluation simulation
  const evaluateCart = async (cart: Cart) => {
    if (isEvaluating) return;
    setIsEvaluating(true);
    setEvaluationResult(null);
    setAnimatedConfidence(0);
    
    // Step 1: Simulate the workflow stages visually
    setEvalProgress('fetching');
    await new Promise((r) => setTimeout(r, 600));
    
    setEvalProgress('rules');
    await new Promise((r) => setTimeout(r, 700));

    setEvalProgress('guardrails');
    await new Promise((r) => setTimeout(r, 700));

    setEvalProgress('outcome');
    await new Promise((r) => setTimeout(r, 500));

    setEvalProgress('saving');

    try {
      const payload = {
        cart_id: cart.id,
        simulate_outcome: cart.simulate_outcome
      };
      
      const res = await fetch(`${BACKEND_URL}/evaluate-cart`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      if (!res.ok) throw new Error('Evaluation failed');
      
      const resultData: AuditRecord = await res.json();
      setEvaluationResult(resultData);
      setEvalProgress('done');

      // Confidence score count-up animation
      const targetConfidence = resultData.decision.confidence_score;
      let start = 0;
      const duration = 800; // ms
      const intervalTime = 20;
      const step = targetConfidence / (duration / intervalTime);
      
      const timer = setInterval(() => {
        start += step;
        if (start >= targetConfidence) {
          setAnimatedConfidence(targetConfidence);
          clearInterval(timer);
        } else {
          setAnimatedConfidence(parseFloat(start.toFixed(2)));
        }
      }, intervalTime);

      // Refresh the audit trail database view
      await refreshAuditRecords();

    } catch (err) {
      console.error(err);
      setEvalProgress('idle');
      setIsEvaluating(false);
    } finally {
      setIsEvaluating(false);
    }
  };

  // Filter carts
  const filteredCarts = carts.filter((c) => {
    const matchesSearch = c.id.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          c.customer_id.toLowerCase().includes(searchQuery.toLowerCase());
    
    if (!matchesSearch) return false;
    
    if (activeFilter === 'ACTIVE_DISCOUNT') return c.has_active_discount;
    if (activeFilter === 'PREVIOUS_DECLINES') return c.declined_upsells_count > 0;
    if (activeFilter === 'HIGH_VALUE') return c.order_value >= 5000;
    
    return true;
  });

  return (
    <div className="min-h-screen bg-darkBg text-slate-100 flex flex-col selection:bg-emerald-500 selection:text-white">
      {/* Header / Hero */}
      <header className="border-b border-slate-800 bg-darkPanel/40 backdrop-blur-md sticky top-0 z-30 px-6 py-4">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="bg-gradient-to-tr from-emerald-500 to-teal-500 p-2.5 rounded-xl shadow-lg shadow-emerald-500/20">
              <ShieldAlert className="w-6 h-6 text-darkBg" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold tracking-tight text-white m-0">VETO</h1>
                <span className="bg-slate-800 text-slate-400 text-xs px-2.5 py-0.5 rounded-full font-mono border border-slate-700">
                  v1.2.0
                </span>
              </div>
              <p className="text-slate-400 text-xs mt-0.5 font-normal">
                Bounded Upsell-Decision Agent & Guardrail Sandbox
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button 
              onClick={fetchData} 
              className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white px-3.5 py-2 rounded-lg text-sm font-medium transition-all border border-slate-700"
            >
              <RefreshCw className="w-4 h-4" />
              Reset Demo
            </button>
          </div>
        </div>
      </header>

      {/* Main Sandbox Layout */}
      <main className="max-w-7xl mx-auto px-4 md:px-6 py-8 flex-1 grid grid-cols-1 lg:grid-cols-12 gap-8 w-full">
        
        {/* Left Column (Stats & Visual Pipeline Diagram) */}
        <div className="lg:col-span-8 space-y-8 flex flex-col">
          
          {/* Hero Architecture Info Panel */}
          <section className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6">
            <div className="flex items-start gap-4">
              <div className="hidden sm:flex bg-slate-800/80 p-3 rounded-lg text-emerald-400">
                <Sparkles className="w-5 h-5" />
              </div>
              <div className="space-y-3">
                <h2 className="text-lg font-semibold text-slate-100 m-0">
                  How VETO Safeguards Checkout Upsells
                </h2>
                <p className="text-slate-400 text-sm leading-relaxed">
                  Unlike traditional checkout modules that spam aggressive popups, VETO feeds Razorpay checkout events through an structured LangGraph pipeline. Decisions are checked against confidence levels, penalized for prior customer declines, and strictly filtered by a conflict check before being recorded to SQLite.
                </p>
                
                {/* Embedded SVG Architecture Flow Diagram */}
                <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-5 mt-4">
                  <h3 className="text-xs font-mono tracking-widest text-slate-500 uppercase mb-4 text-center">
                    Decision Gating Pipeline Architecture
                  </h3>
                  <div className="flex flex-col md:flex-row items-center justify-between gap-3 text-xs font-mono text-slate-400">
                    
                    <div className="flex flex-col items-center p-3 bg-slate-900 border border-slate-800 rounded-lg w-full md:w-32 text-center relative group">
                      <ShoppingCart className="w-5 h-5 text-indigo-400 mb-1.5" />
                      <span className="text-slate-200">1. Cart Fetch</span>
                      <span className="text-[10px] text-slate-500 mt-1">Razorpay API</span>
                    </div>

                    <ArrowRight className="hidden md:block w-4 h-4 text-slate-700" />
                    
                    <div className="flex flex-col items-center p-3 bg-slate-900 border border-slate-800 rounded-lg w-full md:w-36 text-center relative group">
                      <Sliders className="w-5 h-5 text-blue-400 mb-1.5" />
                      <span className="text-slate-200">2. Rules Engine</span>
                      <span className="text-[10px] text-slate-500 mt-1">Confidence Score</span>
                    </div>

                    <ArrowRight className="hidden md:block w-4 h-4 text-slate-700" />

                    <div className="flex flex-col items-center p-3 bg-slate-900 border border-slate-800 rounded-lg w-full md:w-40 text-center relative group">
                      <ShieldAlert className="w-5 h-5 text-amber-500 mb-1.5" />
                      <span className="text-slate-200">3. Guardrail Gate</span>
                      <span className="text-[10px] text-slate-500 mt-1">Discount & Conf checks</span>
                    </div>

                    <ArrowRight className="hidden md:block w-4 h-4 text-slate-700" />

                    <div className="flex flex-col items-center p-3 bg-slate-900 border border-slate-800 rounded-lg w-full md:w-32 text-center relative group">
                      <Database className="w-5 h-5 text-emerald-400 mb-1.5" />
                      <span className="text-slate-200">4. Audit Log</span>
                      <span className="text-[10px] text-slate-500 mt-1">SQLite Trace</span>
                    </div>

                  </div>
                </div>

              </div>
            </div>
          </section>

          {/* Batch Metrics / Analytics Panel */}
          <section className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 space-y-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Activity className="w-5 h-5 text-emerald-400" />
                <h2 className="text-lg font-semibold text-slate-100 m-0">
                  Batch Run Summary (50 Carts)
                </h2>
              </div>
              <span className="text-xs bg-slate-800 text-slate-400 border border-slate-700 px-2 py-1 rounded font-mono">
                data/batch_results.json
              </span>
            </div>

            {isLoadingBatch ? (
              <div className="h-44 flex items-center justify-center text-slate-500 text-sm">
                <RefreshCw className="w-5 h-5 animate-spin mr-2" /> Loading stats...
              </div>
            ) : batchResults ? (
              <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
                
                {/* Stats Counters */}
                <div className="md:col-span-5 grid grid-cols-2 gap-4">
                  <div className="bg-slate-950/50 border border-slate-800/60 p-4 rounded-xl flex flex-col justify-between">
                    <span className="text-slate-400 text-xs flex items-center gap-1.5">
                      <TrendingUp className="w-3.5 h-3.5 text-emerald-500" />
                      AOV Uplift
                    </span>
                    <span className="text-2xl font-bold font-mono text-emerald-400 mt-2">
                      +{batchResults.uplift_percentage}%
                    </span>
                  </div>

                  <div className="bg-slate-950/50 border border-slate-800/60 p-4 rounded-xl flex flex-col justify-between">
                    <span className="text-slate-400 text-xs flex items-center gap-1.5">
                      <ShieldAlert className="w-3.5 h-3.5 text-amber-500" />
                      Decline Rate
                    </span>
                    <span className="text-2xl font-bold font-mono text-amber-500 mt-2">
                      {batchResults.decline_rate_pct}%
                    </span>
                  </div>

                  <div className="bg-slate-950/50 border border-slate-800/60 p-4 rounded-xl flex flex-col justify-between">
                    <span className="text-slate-400 text-xs">Total Propose</span>
                    <span className="text-xl font-bold font-mono text-slate-200 mt-2">
                      {batchResults.total_propose}
                    </span>
                  </div>

                  <div className="bg-slate-950/50 border border-slate-800/60 p-4 rounded-xl flex flex-col justify-between">
                    <span className="text-slate-400 text-xs">Total Decline</span>
                    <span className="text-xl font-bold font-mono text-slate-200 mt-2">
                      {batchResults.total_decline}
                    </span>
                  </div>
                </div>

                {/* Decline Reasons Breakdown Bar Chart */}
                <div className="md:col-span-7 bg-slate-950/50 border border-slate-800/60 p-5 rounded-xl space-y-4">
                  <h3 className="text-xs font-mono tracking-wider text-slate-500 uppercase m-0">
                    Decline Reasons Breakdown
                  </h3>
                  
                  <div className="space-y-3">
                    {/* No Rules Triggered */}
                    <div className="space-y-1">
                      <div className="flex justify-between text-xs font-mono">
                        <span className="text-slate-300">No Rules Triggered</span>
                        <span className="text-slate-400">{batchResults.decline_reasons_breakdown["No rules triggered"]} carts</span>
                      </div>
                      <div className="w-full bg-slate-900 rounded-full h-2 border border-slate-800 overflow-hidden">
                        <div 
                          className="bg-slate-500 h-full rounded-full transition-all duration-1000"
                          style={{ width: `${(batchResults.decline_reasons_breakdown["No rules triggered"] / batchResults.total_decline) * 100}%` }}
                        />
                      </div>
                    </div>

                    {/* Discount Conflict */}
                    <div className="space-y-1">
                      <div className="flex justify-between text-xs font-mono">
                        <span className="text-slate-300">Active Discount Conflict</span>
                        <span className="text-slate-400">{batchResults.decline_reasons_breakdown["Discount conflict"]} carts</span>
                      </div>
                      <div className="w-full bg-slate-900 rounded-full h-2 border border-slate-800 overflow-hidden">
                        <div 
                          className="bg-declineAmber h-full rounded-full transition-all duration-1000"
                          style={{ width: `${(batchResults.decline_reasons_breakdown["Discount conflict"] / batchResults.total_decline) * 100}%` }}
                        />
                      </div>
                    </div>

                    {/* Below Confidence Threshold */}
                    <div className="space-y-1">
                      <div className="flex justify-between text-xs font-mono">
                        <span className="text-slate-300">Confidence Score &lt; 0.65</span>
                        <span className="text-slate-400">{batchResults.decline_reasons_breakdown["Below confidence threshold"]} carts</span>
                      </div>
                      <div className="w-full bg-slate-900 rounded-full h-2 border border-slate-800 overflow-hidden">
                        <div 
                          className="bg-declineRed h-full rounded-full transition-all duration-1000"
                          style={{ width: `${(batchResults.decline_reasons_breakdown["Below confidence threshold"] / batchResults.total_decline) * 100}%` }}
                        />
                      </div>
                    </div>
                  </div>

                </div>

              </div>
            ) : (
              <div className="h-44 flex items-center justify-center text-slate-500 text-sm border border-dashed border-slate-800 rounded-xl">
                Batch results file not loaded. Run `run_batch.py` script.
              </div>
            )}
          </section>

          {/* Interactive Result Dashboard Reveal */}
          <AnimatePresence mode="wait">
            {evalProgress !== 'idle' && (
              <motion.section 
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 space-y-6"
              >
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
                  <h2 className="text-lg font-semibold text-slate-100 m-0 flex items-center gap-2">
                    <Activity className="w-5 h-5 text-blue-400 animate-pulse" />
                    Live Execution Pipeline
                  </h2>
                  <span className="text-xs text-slate-500 font-mono">
                    Cart ID: {selectedCart?.id}
                  </span>
                </div>

                {/* Animated progress flow */}
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-xs font-mono text-center">
                  {[
                    { state: 'fetching', label: '1. Fetching Cart' },
                    { state: 'rules', label: '2. Rules Calc' },
                    { state: 'guardrails', label: '3. Guardrail Check' },
                    { state: 'outcome', label: '4. Outcome Sim' },
                    { state: 'saving', label: '5. DB Committing' }
                  ].map((step) => {
                    const statesOrder = ['idle', 'fetching', 'rules', 'guardrails', 'outcome', 'saving', 'done'];
                    const currentIdx = statesOrder.indexOf(evalProgress);
                    const stepIdx = statesOrder.indexOf(step.state);
                    const isActive = evalProgress === step.state;
                    const isCompleted = currentIdx > stepIdx || evalProgress === 'done';

                    return (
                      <div 
                        key={step.state}
                        className={`p-2.5 rounded-lg border transition-all ${
                          isActive 
                            ? 'bg-blue-900/20 border-blue-500 text-blue-300 font-bold shadow-md shadow-blue-500/10'
                            : isCompleted
                              ? 'bg-slate-950/60 border-slate-800 text-emerald-400'
                              : 'bg-slate-950/20 border-slate-800/40 text-slate-600'
                        }`}
                      >
                        <div className="truncate">{step.label}</div>
                      </div>
                    );
                  })}
                </div>

                {/* Outcome Display */}
                {evalProgress === 'done' && evaluationResult && (
                  <motion.div 
                    initial={{ opacity: 0, scale: 0.98 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className={`rounded-xl border p-5 flex flex-col md:flex-row items-center justify-between gap-6 ${
                      evaluationResult.decision.decision_type === 'PROPOSE'
                        ? 'bg-emerald-950/20 border-emerald-800 text-emerald-100'
                        : 'bg-amber-950/20 border-amber-800 text-amber-100'
                    }`}
                  >
                    <div className="space-y-3 flex-1">
                      <div className="flex items-center gap-2">
                        {evaluationResult.decision.decision_type === 'PROPOSE' ? (
                          <CheckCircle className="w-6 h-6 text-proposeGreen" />
                        ) : (
                          <XCircle className="w-6 h-6 text-declineAmber" />
                        )}
                        <span className="font-bold text-lg font-mono">
                          {evaluationResult.decision.decision_type}ED
                        </span>
                      </div>
                      
                      <div className="text-sm space-y-1.5 font-normal">
                        <p className="text-slate-300">
                          <strong className="text-slate-200">Rule Triggered:</strong>{' '}
                          <code className="text-xs bg-slate-950 border border-slate-850/60 text-slate-300 py-0.5 px-1.5 rounded">
                            {evaluationResult.decision.rule_triggered || 'None'}
                          </code>
                        </p>
                        <p className="text-slate-300">
                          <strong className="text-slate-200">Gate Reason:</strong>{' '}
                          {evaluationResult.decision.reason}
                        </p>
                        {evaluationResult.outcome && (
                          <p className="text-slate-300">
                            <strong className="text-slate-200">Simulated Outcome:</strong>{' '}
                            {evaluationResult.outcome.accepted ? (
                              <span className="text-proposeGreen font-semibold">Accepted (value increased by ₹{evaluationResult.outcome.order_value_delta})</span>
                            ) : (
                              <span className="text-slate-400 font-semibold">Declined (value unchanged)</span>
                            )}
                          </p>
                        )}
                      </div>
                    </div>

                    {/* Confidence Score Big Circle */}
                    <div className="flex flex-col items-center justify-center p-4 bg-slate-950/80 rounded-xl border border-slate-800/80 w-32 h-32 shrink-0">
                      <span className="text-xs text-slate-500 font-mono">CONFIDENCE</span>
                      <span className="text-3xl font-bold font-mono text-white mt-1">
                        {animatedConfidence}
                      </span>
                      <div className="w-16 bg-slate-900 rounded-full h-1 mt-2 overflow-hidden border border-slate-800">
                        <div 
                          className="bg-indigo-500 h-full rounded-full"
                          style={{ width: `${animatedConfidence * 100}%` }}
                        />
                      </div>
                    </div>
                  </motion.div>
                )}
              </motion.section>
            )}
          </AnimatePresence>

          {/* Audit Timeline Section */}
          <section className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 space-y-6 flex-1 flex flex-col">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
              <div className="flex items-center gap-2">
                <Database className="w-5 h-5 text-emerald-400" />
                <h2 className="text-lg font-semibold text-slate-100 m-0">
                  SQLite Audit Trail
                </h2>
              </div>
              <button 
                onClick={refreshAuditRecords}
                disabled={isRefreshingLogs}
                className="text-xs text-slate-400 hover:text-white flex items-center gap-1.5 px-2.5 py-1 bg-slate-800/80 border border-slate-700/60 rounded"
              >
                <RefreshCw className={`w-3 h-3 ${isRefreshingLogs ? 'animate-spin' : ''}`} />
                Refresh Trail
              </button>
            </div>

            {auditRecords.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center text-slate-500 p-8 border border-dashed border-slate-800 rounded-xl">
                <Database className="w-8 h-8 text-slate-700 mb-2" />
                <p className="text-sm">Audit trail is currently empty.</p>
                <p className="text-xs text-slate-600 mt-1">Select and run a cart above to write logs to SQLite.</p>
              </div>
            ) : (
              <div className="space-y-4 max-h-[400px] overflow-y-auto pr-2">
                {auditRecords.map((record) => {
                  const isExpanded = expandedRecord === record.id;
                  const isPropose = record.decision.decision_type === 'PROPOSE';

                  return (
                    <div 
                      key={record.id}
                      className="border border-slate-800 bg-slate-950/40 rounded-xl overflow-hidden hover:border-slate-700/80 transition-colors"
                    >
                      {/* Summary Row */}
                      <div 
                        onClick={() => setExpandedRecord(isExpanded ? null : record.id)}
                        className="p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 cursor-pointer"
                      >
                        <div className="flex items-center gap-3">
                          <div className={`p-1.5 rounded-lg border ${
                            isPropose 
                              ? 'bg-emerald-950/30 border-emerald-800/50 text-emerald-400' 
                              : 'bg-amber-950/30 border-amber-800/50 text-amber-500'
                          }`}>
                            {isPropose ? <CheckCircle className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-semibold text-sm text-slate-200">
                                {isPropose ? 'PROPOSE' : 'DECLINE'}
                              </span>
                              <span className="text-xs text-slate-500 font-mono">
                                {record.cart_id}
                              </span>
                            </div>
                            <p className="text-xs text-slate-400 mt-0.5">
                              {record.decision.reason}
                            </p>
                          </div>
                        </div>

                        <div className="flex items-center gap-3 text-xs font-mono text-slate-500 self-end sm:self-auto">
                          <div className="flex items-center gap-1 bg-slate-900 border border-slate-800 px-2 py-0.5 rounded">
                            <Sliders className="w-3 h-3" />
                            conf: {record.decision.confidence_score}
                          </div>
                          <div className="flex items-center gap-1">
                            <Clock className="w-3.5 h-3.5" />
                            {new Date(parseFloat(record.timestamp) * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                          </div>
                          {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                        </div>
                      </div>

                      {/* Expandable JSON Detail */}
                      {isExpanded && (
                        <div className="border-t border-slate-800/80 bg-slate-950/80 p-4 font-mono text-xs overflow-x-auto">
                          <h4 className="text-[10px] text-slate-500 uppercase tracking-wider mb-2 font-mono">
                            Full SQLite Audit Record JSON Trace
                          </h4>
                          <pre className="text-slate-300 leading-relaxed max-h-60 overflow-y-auto">
                            {JSON.stringify(record, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </section>

        </div>

        {/* Right Column (Cart Picker List) */}
        <div className="lg:col-span-4 space-y-6">
          <section className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-5 space-y-4 flex flex-col max-h-[85vh]">
            <div className="flex items-center gap-2">
              <ShoppingCart className="w-5 h-5 text-emerald-400" />
              <h2 className="text-lg font-semibold text-slate-100 m-0">
                Select Synthetic Cart
              </h2>
            </div>

            {/* Search and Filters */}
            <div className="space-y-3">
              <div className="relative">
                <Search className="w-4 h-4 text-slate-500 absolute left-3 top-3.5" />
                <input 
                  type="text"
                  placeholder="Search by ID or customer ID..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 focus:border-emerald-500/50 rounded-xl py-2.5 pl-9 pr-4 text-sm text-slate-100 placeholder-slate-500 focus:outline-none transition-colors"
                />
              </div>

              {/* Filters list */}
              <div className="flex flex-wrap gap-1.5">
                {[
                  { id: 'ALL', label: 'All Carts' },
                  { id: 'ACTIVE_DISCOUNT', label: 'Discounted' },
                  { id: 'PREVIOUS_DECLINES', label: 'Prior Declines' },
                  { id: 'HIGH_VALUE', label: 'High Value (AOV >= 5k)' }
                ].map((f) => (
                  <button 
                    key={f.id}
                    onClick={() => setActiveFilter(f.id as any)}
                    className={`text-xs px-2.5 py-1 rounded transition-colors ${
                      activeFilter === f.id 
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                        : 'bg-slate-800/60 text-slate-400 hover:text-white border border-slate-700/60'
                    }`}
                  >
                    {f.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Carts List View */}
            <div className="flex-1 overflow-y-auto space-y-2.5 pr-1.5 min-h-[300px]">
              {isLoadingCarts ? (
                <div className="h-40 flex items-center justify-center text-slate-500 text-sm">
                  <RefreshCw className="w-4 h-4 animate-spin mr-2" /> Loading seed carts...
                </div>
              ) : filteredCarts.length === 0 ? (
                <div className="h-40 flex items-center justify-center text-slate-600 text-sm">
                  No matching carts found.
                </div>
              ) : (
                filteredCarts.map((cart) => {
                  const isSelected = selectedCart?.id === cart.id;
                  
                  // Quick check on which rule might trigger
                  let potentialRule = "None";
                  const itemIds = cart.items.map(i => i.id);
                  if (itemIds.includes("item_A") && !itemIds.includes("item_B") && cart.order_value >= 1000) {
                    potentialRule = "bundle_completion";
                  } else if (cart.order_value >= 5000) {
                    potentialRule = "high_value_threshold";
                  } else if (cart.items.some(i => cart.purchase_history.includes(i.category))) {
                    potentialRule = "repeat_customer_affinity";
                  }

                  return (
                    <div 
                      key={cart.id}
                      onClick={() => setSelectedCart(cart)}
                      className={`p-3.5 border rounded-xl cursor-pointer transition-all ${
                        isSelected 
                          ? 'bg-emerald-950/10 border-emerald-500 text-white shadow-md shadow-emerald-500/5'
                          : 'bg-slate-950/40 border-slate-800/80 text-slate-300 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="flex items-center gap-1.5">
                            <span className="font-semibold text-sm text-slate-100">
                              {cart.id}
                            </span>
                            {/* Original Labeled subset indicator */}
                            {cart.id.startsWith("cart_scenario_") && (
                              <span className="bg-slate-800 text-slate-400 border border-slate-700/60 text-[9px] px-1 rounded uppercase tracking-wider font-mono">
                                Core scenario
                              </span>
                            )}
                          </div>
                          <span className="text-[11px] text-slate-500 block font-mono mt-0.5">
                            Customer: {cart.customer_id}
                          </span>
                        </div>
                        <span className="font-mono text-sm font-bold text-white">
                          ₹{cart.order_value}
                        </span>
                      </div>

                      {/* Items preview tag */}
                      <div className="flex flex-wrap gap-1 mt-2.5">
                        {cart.items.map((it) => (
                          <span key={it.id} className="bg-slate-900 border border-slate-800/80 text-[10px] text-slate-400 px-1.5 py-0.5 rounded font-mono">
                            {it.id} ({it.category || 'misc'})
                          </span>
                        ))}
                      </div>

                      {/* Info indicators */}
                      <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono border-t border-slate-800/40 mt-3 pt-2">
                        <div className="flex items-center gap-2">
                          <span className={cart.has_active_discount ? 'text-amber-500' : 'text-slate-600'}>
                            Disc: {cart.has_active_discount ? 'Y' : 'N'}
                          </span>
                          <span className={cart.declined_upsells_count > 0 ? 'text-red-400' : 'text-slate-600'}>
                            Declines: {cart.declined_upsells_count}
                          </span>
                        </div>
                        <span className="text-[10px] text-slate-400">
                          Target: {potentialRule}
                        </span>
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            {/* CTA Execution Button */}
            {selectedCart && (
              <div className="border-t border-slate-800/80 pt-4 mt-auto">
                <button 
                  onClick={() => evaluateCart(selectedCart)}
                  disabled={isEvaluating}
                  className="w-full bg-emerald-500 hover:bg-emerald-400 disabled:bg-slate-800 text-slate-950 disabled:text-slate-500 font-semibold py-3 px-4 rounded-xl flex items-center justify-center gap-2 transition-colors focus:outline-none text-sm cursor-pointer shadow-lg shadow-emerald-500/10"
                >
                  {isEvaluating ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      Evaluating Decision...
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4 fill-current" />
                      Run Cart Decision Pipeline
                    </>
                  )}
                </button>
              </div>
            )}
          </section>
        </div>

      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/60 bg-slate-950/20 py-6 text-center text-xs text-slate-500 font-mono mt-8">
        VETO Upsell-Decision Bounded Agent — Sandbox Dashboard Demo Mode
      </footer>
    </div>
  );
}
