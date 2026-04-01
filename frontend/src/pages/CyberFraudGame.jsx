import React, { useState, useEffect, Suspense, useRef } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Stars, Sparkles, OrbitControls, Html, Float } from '@react-three/drei'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'
import '../index.css' // Import standard styles

// Assuming global api url matches other pages
const API_BASE_URL = '/api/game'

// Custom spinning 3D geometric prop for aesthetic interaction
const HologramSphere = ({ isProcessing }) => {
  const meshRef = useRef()
  useFrame((state, delta) => {
    if (meshRef.current) {
      meshRef.current.rotation.x += delta * (isProcessing ? 3.5 : 0.5)
      meshRef.current.rotation.y += delta * (isProcessing ? 3.0 : 0.4)
    }
  })

  return (
    <Float speed={2} rotationIntensity={1.5} floatIntensity={2}>
      <mesh ref={meshRef} position={[0, 0, -3]}>
        <icosahedronGeometry args={[2.5, 1]} />
        <meshStandardMaterial 
          color={isProcessing ? "#ef4444" : "#6366f1"} 
          wireframe
          emissive={isProcessing ? "#ef4444" : "#6366f1"}
          emissiveIntensity={isProcessing ? 2.5 : 0.8}
          transparent
          opacity={0.4}
        />
      </mesh>
    </Float>
  )
}

const CyberFraudGame = () => {
  const [scenario, setScenario] = useState(null)
  const [loading, setLoading] = useState(false)
  const [evaluating, setEvaluating] = useState(false)
  const [result, setResult] = useState(null)
  const [score, setScore] = useState(0)
  const [errorMessage, setErrorMessage] = useState("")
  
  // Custom Mode Logic
  const [isCustomMode, setIsCustomMode] = useState(false)
  const [customInput, setCustomInput] = useState({
    age: 24, years_worked: 2, 
    monthly_income: 40000, monthly_expenses: 30000, 
    estimated_emi_payments: 0,
    non_ancestral_property_value: 2000000, ancestral_property_value: 28000000,
    reported_savings: 100000,
    location_tier: 1, housing_type: 1, dependents: 0
  })

  const toggleCustomMode = () => {
    setIsCustomMode(!isCustomMode)
    setScenario(null)
    setResult(null)
  }

  const customEvaluate = async (userGuessFraud) => {
    if (evaluating) return
    setEvaluating(true)
    try {
      const payload = {
        age: Number(customInput.age),
        years_worked: Number(customInput.years_worked),
        monthly_income: Number(customInput.monthly_income),
        monthly_expenses: Number(customInput.monthly_expenses),
        estimated_emi_payments: Number(customInput.estimated_emi_payments),
        ancestral_property_value: Number(customInput.ancestral_property_value),
        non_ancestral_property_value: Number(customInput.non_ancestral_property_value),
        total_property_value: Number(customInput.ancestral_property_value) + Number(customInput.non_ancestral_property_value),
        location_tier: Number(customInput.location_tier),
        housing_type: Number(customInput.housing_type),
        reported_savings: Number(customInput.reported_savings),
        dependents: Number(customInput.dependents),
        user_guess_fraud: userGuessFraud
      }
      const res = await axios.post(`${API_BASE_URL}/evaluate`, payload)
      if (res.data.status === 'success') {
        const finalData = res.data.result
        setResult(finalData)
        setScore(prev => prev + finalData.score_awarded)
      }
    } catch (err) {
      console.error("Failed to evaluate custom scenario", err)
      alert("ML Engine offline.")
    } finally {
      setEvaluating(false)
    }
  }

  const loadScenario = async () => {
    try {
      setLoading(true)
      setErrorMessage("")
      setResult(null)
      const res = await axios.get(`${API_BASE_URL}/scenario`)
      if (res.data.status === 'success') {
        setScenario(res.data.scenario)
      }
    } catch (err) {
      console.error("Failed to fetch scenario", err)
      setErrorMessage("Machine Learning connection failed. Ensure your Python backend (Uvicorn) is restarted and actively running.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // Await explicit user start interaction instead of auto-loading to prevent silent mounting crashes.
  }, [])

  const handleDecision = async (userGuessFraud) => {
    if (evaluating || !scenario) return
    setEvaluating(true)
    
    try {
      const payload = {
        ...scenario,
        user_guess_fraud: userGuessFraud
      }
      const res = await axios.post(`${API_BASE_URL}/evaluate`, payload)
      if (res.data.status === 'success') {
        const finalData = res.data.result
        setResult(finalData)
        setScore(prev => prev + finalData.score_awarded)
      }
    } catch (err) {
      console.error("Failed to evaluate via XGBoost backend", err)
      alert("ML Engine offline. Ensure the FastAPI Python module is loaded.")
    } finally {
      setEvaluating(false)
    }
  }

  const formatCurrency = (amt) => {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(amt)
  }

  return (
    <div className="game-container" style={{ width: '100vw', height: '100vh', background: '#09090b', position: 'relative', overflow: 'hidden' }}>
      
      {/* 3D Cybernetic Background Canvas */}
      <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', pointerEvents: 'none' }}>
        <Canvas camera={{ position: [0, 0, 5], fov: 60 }}>
          <ambientLight intensity={0.5} />
          <pointLight position={[10, 10, 10]} color="#4f46e5" intensity={1.5} />
          <pointLight position={[-10, -10, -10]} color="#ec4899" intensity={1} />
          
          <Suspense fallback={null}>
            <Stars radius={100} depth={50} count={3000} factor={4} saturation={1} fade speed={1} />
            <Sparkles count={50} scale={10} size={5} speed={0.4} opacity={0.3} color="#fff" />
            <HologramSphere isProcessing={evaluating} />
          </Suspense>
        </Canvas>
      </div>

      {/* Floating UI Overlays */}
      <div className="container" style={{ position: 'relative', zIndex: 10, height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', paddingTop: '4rem' }}>
        
        <header style={{ display: 'flex', justifyContent: 'space-between', width: '100%', maxWidth: '800px', marginBottom: '2rem' }}>
          <div>
            <h1 style={{ color: '#fff', fontSize: '2.5rem', fontWeight: 800, textShadow: '0 0 20px rgba(99, 102, 241, 0.5)' }}>CYBER-AUDITOR 3D</h1>
            <p style={{ color: '#a1a1aa' }}>Beat the Scikit-Learn Machine Learning Algorithm</p>
            <button 
              onClick={toggleCustomMode}
              style={{ marginTop: '0.5rem', background: isCustomMode ? '#ec4899' : '#3730a3', color: '#fff', border: 'none', padding: '0.4rem 1rem', borderRadius: '8px', cursor: 'pointer', fontSize: '0.85rem', fontWeight: 'bold' }}
            >
              Mode: {isCustomMode ? 'CUSTOM INPUT SANDBOX' : 'RANDOM SYNTHETIC TARGETS'} ⇄
            </button>
          </div>
          <div style={{ background: 'rgba(99, 102, 241, 0.1)', padding: '1rem 2rem', borderRadius: '15px', border: '1px solid rgba(99, 102, 241, 0.3)' }}>
            <span style={{ color: '#a1a1aa', fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '1px' }}>Total Score</span>
            <h2 style={{ color: '#fff', fontSize: '2rem', margin: 0 }}>{score}</h2>
          </div>
        </header>

        {loading ? (
          <div className="spinner"></div>
        ) : errorMessage ? (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ background: 'rgba(239, 68, 68, 0.2)', padding: '2rem', borderRadius: '15px', border: '1px solid #ef4444', textAlign: 'center' }}>
            <h3 style={{ color: '#f87171' }}>⚠️ Connection Error</h3>
            <p style={{ color: '#fca5a5' }}>{errorMessage}</p>
            <button onClick={loadScenario} style={{ marginTop: '1rem', padding: '0.8rem 2rem', background: '#ef4444', color: '#fff', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}>RETRY CONNECTION</button>
          </motion.div>
        ) : isCustomMode && !result ? (
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} style={{ background: 'rgba(15, 23, 42, 0.9)', backdropFilter: 'blur(20px)', border: '1px solid #3b82f6', borderRadius: '20px', padding: '2.5rem', width: '100%', maxWidth: '800px', boxShadow: '0 25px 50px -12px rgba(59, 130, 246, 0.25)' }}>
            <h3 style={{ color: '#fff', margin: '0 0 1.5rem 0', textTransform: 'uppercase', letterSpacing: '2px', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '1rem' }}>Construct Custom Target Dossier</h3>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', color: '#e2e8f0', fontSize: '0.95rem' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                <label>Target Age</label>
                <input type="number" value={customInput.age} onChange={(e) => setCustomInput({...customInput, age: e.target.value})} style={{ background: '#1e293b', border: '1px solid #475569', color: '#fff', padding: '0.8rem', borderRadius: '8px' }} />
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                <label>Years Active Employment</label>
                <input type="number" value={customInput.years_worked} onChange={(e) => setCustomInput({...customInput, years_worked: e.target.value})} style={{ background: '#1e293b', border: '1px solid #475569', color: '#fff', padding: '0.8rem', borderRadius: '8px' }} />
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                <label>Monthly Salary (Income)</label>
                <input type="number" value={customInput.monthly_income} onChange={(e) => setCustomInput({...customInput, monthly_income: e.target.value})} style={{ background: '#1e293b', border: '1px solid #475569', color: '#fff', padding: '0.8rem', borderRadius: '8px' }} />
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                <label>Monthly Expenditure</label>
                <input type="number" value={customInput.monthly_expenses} onChange={(e) => setCustomInput({...customInput, monthly_expenses: e.target.value})} style={{ background: '#1e293b', border: '1px solid #475569', color: '#fff', padding: '0.8rem', borderRadius: '8px' }} />
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                <label>Monthly EMI Paid</label>
                <input type="number" value={customInput.estimated_emi_payments} onChange={(e) => setCustomInput({...customInput, estimated_emi_payments: e.target.value})} style={{ background: '#1e293b', border: '1px solid #475569', color: '#fff', padding: '0.8rem', borderRadius: '8px' }} />
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                <label>Total Savings Cache</label>
                <input type="number" value={customInput.reported_savings} onChange={(e) => setCustomInput({...customInput, reported_savings: e.target.value})} style={{ background: '#1e293b', border: '1px solid #475569', color: '#fff', padding: '0.8rem', borderRadius: '8px' }} />
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                <label style={{ color: '#fb923c', fontWeight: 'bold' }}>Ancestral Property Value (Inherited)</label>
                <input type="number" value={customInput.ancestral_property_value} onChange={(e) => setCustomInput({...customInput, ancestral_property_value: e.target.value})} style={{ background: 'rgba(251, 146, 60, 0.1)', border: '1px solid #fb923c', color: '#fff', padding: '0.8rem', borderRadius: '8px' }} />
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                <label style={{ color: '#fca5a5', fontWeight: 'bold' }}>Non-Ancestral Property (Purchased)</label>
                <input type="number" value={customInput.non_ancestral_property_value} onChange={(e) => setCustomInput({...customInput, non_ancestral_property_value: e.target.value})} style={{ background: 'rgba(248, 113, 113, 0.1)', border: '1px solid #f87171', color: '#fff', padding: '0.8rem', borderRadius: '8px' }} />
              </div>
            </div>

            <div style={{ display: 'flex', gap: '1rem', width: '100%', marginTop: '2rem' }}>
              <button onClick={() => customEvaluate(false)} disabled={evaluating} style={{ flex: 1, padding: '1.2rem', background: 'rgba(16, 185, 129, 0.15)', color: '#34d399', border: '1px solid #10b981', borderRadius: '15px', fontWeight: 'bold', cursor: 'pointer', transition: 'all 0.2s' }}>
                 TEST AI (Expect NO Fraud)
              </button>
              <button onClick={() => customEvaluate(true)} disabled={evaluating} style={{ flex: 1, padding: '1.2rem', background: 'rgba(239, 68, 68, 0.15)', color: '#f87171', border: '1px solid #ef4444', borderRadius: '15px', fontWeight: 'bold', cursor: 'pointer', transition: 'all 0.2s' }}>
                 TEST AI (Expect FRAUD)
              </button>
            </div>
          </motion.div>
        ) : !scenario && !result && !isCustomMode ? (
          <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} style={{ textAlign: 'center', marginTop: '4rem' }}>
            <button 
              onClick={loadScenario}
              style={{ padding: '1.5rem 4rem', background: 'linear-gradient(45deg, #4f46e5, #ec4899)', color: '#fff', border: 'none', borderRadius: '50px', fontSize: '1.5rem', fontWeight: '900', letterSpacing: '2px', cursor: 'pointer', boxShadow: '0 0 40px rgba(236, 72, 153, 0.5)' }}
            >
              START 3D SIMULATION
            </button>
          </motion.div>
        ) : scenario && !result ? (
          <motion.div 
            initial={{ opacity: 0, y: 50 }} animate={{ opacity: 1, y: 0 }}
            style={{ background: 'rgba(24, 24, 27, 0.7)', backdropFilter: 'blur(20px)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '24px', padding: '3rem', width: '100%', maxWidth: '800px', boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
              <h3 style={{ color: '#fff', margin: 0 }}>Target Dossier Extracted</h3>
              <span style={{ background: '#3730a3', color: '#c7d2fe', padding: '0.5rem 1rem', borderRadius: '100px', fontSize: '0.9rem' }}>Tier {scenario.location_tier} Region</span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem', marginBottom: '3rem' }}>
              <div>
                <Label>Demographics</Label>
                <Data>Age {scenario.age} • {scenario.dependents} Dependents</Data>
                <Data>{scenario.years_worked} Years Employment</Data>
              </div>
              <div>
                <Label>Financial Velocity</Label>
                <Data>Income: {formatCurrency(scenario.monthly_income)}/mo</Data>
                <Data>Expenses: {formatCurrency(scenario.monthly_expenses)}/mo {scenario.estimated_emi_payments > 0 ? <span style={{ color: '#93c5fd', fontSize: '0.85em' }}>(Includes EMI)</span> : ''}</Data>
              </div>
              <div style={{ gridColumn: '1 / -1', background: 'rgba(255,255,255,0.03)', padding: '1.5rem', borderRadius: '15px' }}>
                <Label>Asset Declaration</Label>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.5rem' }}>
                  <Data>Savings Cache: {formatCurrency(scenario.reported_savings)}</Data>
                  <Data style={{ color: '#fb923c' }}>Total Property: {formatCurrency(scenario.total_property_value)}</Data>
                </div>
                <div style={{ display: 'flex', gap: '3rem', fontSize: '0.95rem', color: '#a1a1aa', marginTop: '0.5rem', paddingLeft: '1rem', borderLeft: '2px solid rgba(251, 146, 60, 0.4)' }}>
                     <span>Ancestral Heritage: <b style={{ color: '#fff' }}>{formatCurrency(scenario.ancestral_property_value)}</b></span>
                     <span>Recent Non-Ancestral: <b style={{ color: '#fff' }}>{formatCurrency(scenario.non_ancestral_property_value)}</b></span>
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '1rem', width: '100%' }}>
              <button 
                onClick={() => handleDecision(false)}
                disabled={evaluating}
                style={{ flex: 1, padding: '1.25rem', background: 'rgba(16, 185, 129, 0.1)', color: '#34d399', border: '1px solid #10b981', borderRadius: '15px', fontSize: '1.1rem', fontWeight: 'bold', cursor: evaluating ? 'not-allowed' : 'pointer', transition: 'all 0.2s' }}
                onMouseEnter={(e) => e.target.style.background = 'rgba(16, 185, 129, 0.2)'}
                onMouseLeave={(e) => e.target.style.background = 'rgba(16, 185, 129, 0.1)'}
              >
                CLEAR TARGET (Not Fraud)
              </button>
              <button 
                onClick={() => handleDecision(true)}
                disabled={evaluating}
                style={{ flex: 1, padding: '1.25rem', background: 'rgba(239, 68, 68, 0.1)', color: '#f87171', border: '1px solid #ef4444', borderRadius: '15px', fontSize: '1.1rem', fontWeight: 'bold', cursor: evaluating ? 'not-allowed' : 'pointer', transition: 'all 0.2s' }}
                onMouseEnter={(e) => e.target.style.background = 'rgba(239, 68, 68, 0.2)'}
                onMouseLeave={(e) => e.target.style.background = 'rgba(239, 68, 68, 0.1)'}
              >
                FLAG FRAUD ANOMALY
              </button>
            </div>
          </motion.div>
        ) : result ? (
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
            style={{ background: 'rgba(24, 24, 27, 0.85)', backdropFilter: 'blur(30px)', border: `1px solid ${result.user_correct ? '#10b981' : '#ef4444'}`, borderRadius: '24px', padding: '3rem', width: '100%', maxWidth: '800px', boxShadow: `0 0 60px ${result.user_correct ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)'}` }}
          >
            <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
              <h2 style={{ color: result.user_correct ? '#34d399' : '#f87171', fontSize: '2.5rem', margin: '0 0 1rem 0' }}>
                {result.user_correct ? 'SYNCHRONIZED WITH AI!' : 'AI DEVIATION DETECTED'}
              </h2>
              <p style={{ color: '#a1a1aa', fontSize: '1.2rem' }}>You earned +{result.score_awarded} points.</p>
            </div>

            <div style={{ background: 'rgba(0,0,0,0.5)', padding: '2rem', borderRadius: '15px', marginBottom: '2rem' }}>
              <h4 style={{ color: '#fff', margin: '0 0 1rem 0', textTransform: 'uppercase', letterSpacing: '1px' }}>Machine Learning Deep Analysis</h4>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem', paddingBottom: '1.5rem', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                <span style={{ color: '#a1a1aa' }}>Model Fraud Probability:</span>
                <span style={{ color: result.ai_predicted_fraud ? '#f87171' : '#34d399', fontSize: '1.5rem', fontWeight: 'bold' }}>
                  {result.ai_fraud_probability}%
                </span>
              </div>
              
              <h5 style={{ color: '#8b5cf6', marginBottom: '0.8rem', textTransform: 'uppercase', letterSpacing: '1px' }}>Explainable Logical Output</h5>
              <div style={{ background: 'rgba(139, 92, 246, 0.1)', borderLeft: '4px solid #8b5cf6', padding: '1.5rem', borderRadius: '0 10px 10px 0', lineHeight: '1.8', color: '#e4e4e7', fontSize: '1.05rem' }}>
                {result.shap_explanation.map((exp, idx) => (
                  <p key={idx} style={{ margin: idx === 0 ? '0 0 1rem 0' : '0' }}>{exp}</p>
                ))}
              </div>
            </div>

            <button 
              onClick={() => isCustomMode ? setResult(null) : loadScenario()}
              style={{ width: '100%', padding: '1.25rem', background: '#4f46e5', color: '#fff', border: 'none', borderRadius: '15px', fontSize: '1.1rem', fontWeight: 'bold', cursor: 'pointer', transition: 'all 0.2s', boxShadow: '0 10px 25px -5px rgba(79, 70, 229, 0.4)' }}
            >
              {isCustomMode ? 'RUN ANOTHER CUSTOM TEST' : 'REQUEST NEW SCENARIO'}
            </button>
          </motion.div>
        ) : null}

      </div>
    </div>
  )
}

const Label = ({ children }) => <div style={{ color: '#a1a1aa', fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '0.5rem' }}>{children}</div>
const Data = ({ children, style }) => <div style={{ color: '#fff', fontSize: '1.1rem', marginBottom: '0.2rem', ...style }}>{children}</div>

export default CyberFraudGame
