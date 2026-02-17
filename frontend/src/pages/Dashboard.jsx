import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Activity, Leaf, Pill, Stethoscope, LogOut, AlertCircle, BarChart3, Sparkles, CheckCircle2, XCircle, X, ShoppingCart, ShoppingBag, Plus, Minus } from 'lucide-react';

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState("diagnosis"); 
  const [inputText, setInputText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [user, setUser] = useState(null);
  const [showProfile, setShowProfile] = useState(false);
  
  const [pharmacyProducts, setPharmacyProducts] = useState([]);
  const [cart, setCart] = useState([]);
  const [showCart, setShowCart] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const storedUser = localStorage.getItem('currentUser');
    if (storedUser) setUser(JSON.parse(storedUser));
    else navigate('/');

    const fetchMedicines = async () => {
      try {
        const response = await fetch("http://localhost:8000/medicines");
        const data = await response.json();
        setPharmacyProducts(data.products || []);
      } catch (err) {
        console.error("Failed to load pharmacy inventory");
      }
    };
    fetchMedicines();
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem('currentUser');
    navigate('/');
  };

  const handlePredict = async (e) => {
    e.preventDefault();
    if (!inputText) return;
    setLoading(true); setError(""); setResult(null);

    try {
      const response = await fetch("http://localhost:8000/predict", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: inputText, username: user.name }), 
      });
      if (!response.ok) throw new Error("Server Error");
      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError("Failed to connect to the Diagnosis Engine.");
    } finally {
      setLoading(false);
    }
  };

  const addToCart = (product) => {
    const existing = cart.find(item => item.id === product.id);
    if (existing) {
      setCart(cart.map(item => item.id === product.id ? { ...item, qty: item.qty + 1 } : item));
    } else {
      setCart([...cart, { ...product, qty: 1 }]);
    }
  };

  const updateQty = (id, amount) => {
    setCart(cart.map(item => {
      if (item.id === id) return { ...item, qty: Math.max(0, item.qty + amount) };
      return item;
    }).filter(item => item.qty > 0));
  };

  // 🚀 MATH FIX: Strips out the "₹" symbol so math works properly
  const cleanPrice = (priceStr) => {
    if (!priceStr) return 0;
    const num = parseInt(String(priceStr).replace(/\D/g, ''), 10);
    return isNaN(num) ? 0 : num;
  };

  const cartTotal = cart.reduce((total, item) => total + (cleanPrice(item.price) * item.qty), 0);
  const cartCount = cart.reduce((count, item) => count + item.qty, 0);

  // ==========================================================
  // 💳 REAL RAZORPAY INTEGRATION LOGIC
  // ==========================================================
  const loadRazorpayScript = () => {
    return new Promise((resolve) => {
      const script = document.createElement("script");
      script.src = "https://checkout.razorpay.com/v1/checkout.js";
      script.onload = () => resolve(true);
      script.onerror = () => resolve(false);
      document.body.appendChild(script);
    });
  };

  const handlePayment = async () => {
    const res = await loadRazorpayScript();
    if (!res) {
      alert("Razorpay SDK failed to load. Are you online?");
      return;
    }

    try {
      // 1. Ask backend to create a Razorpay Order
      const orderResponse = await fetch("http://localhost:8000/create-order", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ amount: cartTotal }),
      });
      const orderData = await orderResponse.json();

      if (!orderResponse.ok) throw new Error(orderData.detail || "Could not create order");

      // 2. Open the Razorpay Checkout Modal
      const options = {
        key: "rzp_test_SH69Y3GKd8tYN0", // ⚠️ PASTE YOUR rzp_test_ KEY HERE!
        amount: orderData.amount,
        currency: "INR",
        name: "Ayurvedic Pharmacy",
        description: "Intelligent Diagnosis System Checkout",
        image: "https://images.unsplash.com/photo-1512069772995-ec65ed45afd6?auto=format&fit=crop&q=80&w=100", 
        order_id: orderData.order_id,
        handler: async function (response) {
          // 3. Verify Payment on the Backend
          try {
            const verifyRes = await fetch("http://localhost:8000/verify-payment", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                razorpay_order_id: response.razorpay_order_id,
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_signature: response.razorpay_signature,
                cart_items: cart,
                username: user.name,
                total_amount: cartTotal
              }),
            });
            
            if (verifyRes.ok) {
              alert(`Payment Successful! Order ID: ${response.razorpay_payment_id}`);
              setCart([]); 
              setShowCart(false); 
            } else {
              alert("Payment Verification Failed on server.");
            }
          } catch (err) {
             alert("Error verifying payment.");
          }
        },
        prefill: {
          name: user.name,
          email: "patient@example.com",
          contact: "9999999999",
        },
        theme: { color: "#16a34a" }, 
      };

      const paymentObject = new window.Razorpay(options);
      paymentObject.open();
    } catch (err) {
      alert("Error initiating payment. Make sure backend is running and Razorpay keys are valid!");
    }
  };


  if (!user) return null;

  const allPredictions = result && result.disease !== "Unknown" 
    ? [ { disease: result.disease, confidence: result.confidence }, ...(result.alternative_predictions || []) ] : [];

  return (
    <div className="h-screen w-full bg-gray-50 flex flex-col font-sans overflow-hidden">
      
      <header className="bg-white border-b border-green-200 shadow-sm shrink-0">
        <div className="h-20 flex items-center justify-between px-8">
          <div className="flex items-center space-x-3">
            <Leaf className="w-10 h-10 text-green-600" />
            <div>
              <h1 className="text-2xl font-extrabold text-green-800 tracking-tight">Intelligent Diagnosis System</h1>
              <p className="text-xs text-green-600 font-bold uppercase tracking-wider">Patient: {user.name} | {user.age} yrs | {user.gender}</p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <button onClick={() => setShowCart(true)} className="relative p-2 text-gray-600 hover:text-green-600 transition-colors cursor-pointer">
              <ShoppingCart className="w-6 h-6" />
              {cartCount > 0 && <span className="absolute top-0 right-0 bg-red-500 text-white text-[10px] font-bold w-4 h-4 rounded-full flex items-center justify-center">{cartCount}</span>}
            </button>

            {user.ayurvedic_profile && (
              <button onClick={() => setShowProfile(true)} className="flex items-center text-sm font-bold text-emerald-800 bg-emerald-100 hover:bg-emerald-200 border border-emerald-300 px-4 py-2 rounded-lg transition-all shadow-sm">
                <Sparkles className="w-4 h-4 mr-2 text-emerald-600" /> My Ayurvedic Plan
              </button>
            )}
            <button onClick={handleLogout} className="flex items-center text-sm font-bold text-red-500 hover:text-white hover:bg-red-500 border border-red-200 px-4 py-2 rounded-lg transition-all shadow-sm">
              <LogOut className="w-4 h-4 mr-2" /> Logout
            </button>
          </div>
        </div>
        
        <div className="flex px-8 space-x-8 border-t border-gray-100 bg-gray-50/50">
          <button 
            onClick={() => setActiveTab("diagnosis")}
            className={`py-3 font-bold text-sm border-b-2 transition-colors ${activeTab === "diagnosis" ? "border-green-600 text-green-700" : "border-transparent text-gray-500 hover:text-gray-800"}`}
          >
            <Stethoscope className="w-4 h-4 inline mr-2 mb-0.5" /> Symptom Analyzer
          </button>
          <button 
            onClick={() => setActiveTab("pharmacy")}
            className={`py-3 font-bold text-sm border-b-2 transition-colors ${activeTab === "pharmacy" ? "border-green-600 text-green-700" : "border-transparent text-gray-500 hover:text-gray-800"}`}
          >
            <ShoppingBag className="w-4 h-4 inline mr-2 mb-0.5" /> Ayurvedic Pharmacy
          </button>
        </div>
      </header>

      <main className="flex-1 overflow-hidden p-6 md:p-8">
        
        {activeTab === "diagnosis" && (
          <div className="flex flex-col md:flex-row gap-6 h-full">
            <div className={`flex flex-col h-full transition-all duration-500 ${result ? 'w-full md:w-1/3' : 'w-full max-w-3xl mx-auto mt-10'}`}>
              <div className="bg-white p-6 rounded-2xl shadow-lg border border-gray-200 flex flex-col h-full">
                <h2 className="flex text-gray-800 font-extrabold text-xl mb-4 items-center border-b pb-3">
                  <Stethoscope className="w-6 h-6 mr-3 text-blue-500"/> Symptom Analyzer
                </h2>
                <textarea
                  className="w-full flex-1 p-4 border border-gray-300 rounded-xl focus:ring-4 focus:ring-green-500/20 focus:border-green-500 focus:outline-none mb-4 bg-gray-50 text-gray-900 text-lg resize-none"
                  placeholder="Describe your exact symptoms, duration, and severity..."
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                ></textarea>
                <button 
                  onClick={handlePredict} disabled={loading}
                  className="w-full bg-green-600 hover:bg-green-700 text-white font-extrabold py-4 rounded-xl transition-all disabled:bg-gray-400 flex justify-center items-center text-lg shadow-lg"
                >
                  {loading ? <Activity className="animate-spin w-6 h-6 mr-2" /> : "Run Diagnosis Engine"}
                </button>
                {error && <p className="mt-3 text-red-500 text-sm font-bold text-center">{error}</p>}
              </div>
            </div>

            {result && (
              <div className="w-full md:w-2/3 h-full overflow-y-auto pr-2 custom-scrollbar space-y-6 pb-6">
                {result.disease === "Unknown" ? (
                  <div className="bg-amber-50 border-l-4 border-amber-500 p-6 rounded-r-xl shadow-sm">
                    <div className="flex items-start">
                      <AlertCircle className="w-6 h-6 text-amber-600 mr-3 mt-1 shrink-0" />
                      <div>
                        <h3 className="text-lg font-bold text-amber-900">Clarification Needed</h3>
                        <p className="text-amber-800 mt-2 font-medium">{result.follow_up}</p>
                      </div>
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="bg-white border border-gray-200 p-6 rounded-2xl shadow-md">
                      <h3 className="text-lg font-extrabold text-gray-800 flex items-center mb-4 border-b pb-2">
                        <BarChart3 className="w-5 h-5 mr-3 text-blue-500" /> Diagnostic Probabilities
                      </h3>
                      <div className="space-y-4">
                        {allPredictions.map((pred, idx) => (
                          <div key={idx} className={idx === 0 ? "bg-blue-50 p-4 rounded-xl border border-blue-200" : "p-1"}>
                            <div className="flex justify-between items-center mb-1">
                              <span className={`font-extrabold capitalize ${idx === 0 ? 'text-blue-900 text-lg' : 'text-gray-600'}`}>{idx + 1}. {pred.disease}</span>
                              <span className={`font-bold ${idx === 0 ? 'text-blue-700' : 'text-gray-500'}`}>{pred.confidence}%</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div className={`h-2 rounded-full ${idx === 0 ? 'bg-blue-500 shadow-md' : 'bg-gray-400'}`} style={{ width: `${pred.confidence}%` }}></div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="bg-white rounded-2xl shadow-md border border-green-200 overflow-hidden">
                      <div className="bg-green-600 px-6 py-4 flex items-center justify-between">
                        <h2 className="text-xl font-extrabold text-white flex items-center">
                          <Leaf className="w-6 h-6 mr-3 text-green-200" /> Protocol for {result.disease}
                        </h2>
                        <button onClick={() => setActiveTab('pharmacy')} className="text-sm bg-white text-green-700 font-bold px-3 py-1.5 rounded shadow-sm hover:bg-green-50">Buy Medicines</button>
                      </div>
                      <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-8">
                        <div>
                          <h3 className="text-lg font-extrabold text-gray-800 flex items-center mb-4 border-b pb-2">
                            <Pill className="w-5 h-5 mr-2 text-green-500" /> Medicines
                          </h3>
                          <ul className="space-y-3">
                            {result.ayurveda?.medicine_names?.length > 0 ? (
                              result.ayurveda.medicine_names.map((med, idx) => (
                                <li key={idx} className="flex items-center bg-gray-50 p-3 rounded-lg border border-gray-200">
                                  <span className="h-6 w-6 rounded-full bg-green-200 text-green-800 flex items-center justify-center text-xs font-bold mr-3">{idx + 1}</span>
                                  <span className="font-bold text-gray-800">{med}</span>
                                </li>
                              ))
                            ) : <p className="text-sm text-gray-500 italic">No specific medicines.</p>}
                          </ul>
                        </div>
                        <div>
                          <h3 className="text-lg font-extrabold text-gray-800 flex items-center mb-4 border-b pb-2">
                            <AlertCircle className="w-5 h-5 mr-2 text-red-500" /> Precautions
                          </h3>
                          {result.ayurveda?.precautions?.length > 0 ? (
                            <div className="bg-red-50 p-4 rounded-xl border border-red-100">
                              <ul className="list-disc text-sm font-medium text-red-900 space-y-2 ml-4">
                                {result.ayurveda.precautions.map((tip, idx) => <li key={idx}>{tip}</li>)}
                              </ul>
                            </div>
                          ) : <p className="text-sm text-gray-500 italic">No specific precautions.</p>}
                        </div>
                      </div>
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
        )}

        {activeTab === "pharmacy" && (
          <div className="h-full overflow-y-auto custom-scrollbar pb-10 max-w-7xl mx-auto">
            <div className="mb-8 flex justify-between items-center">
              <div>
                <h2 className="text-3xl font-black text-gray-900 mb-2">Ayurvedic Pharmacy</h2>
                <p className="text-gray-600">Purchase pure, certified Ayurvedic medicines derived from our medical knowledge base.</p>
              </div>
              {pharmacyProducts.length === 0 && <Activity className="animate-spin w-8 h-8 text-green-600" />}
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {pharmacyProducts.map(product => (
                <div key={product.id} className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-lg transition-shadow flex flex-col">
                  <div className="w-full h-48 bg-gray-100 flex items-center justify-center overflow-hidden">
                    <img 
                      src={product.image} 
                      alt={product.name} 
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        e.target.onerror = null; 
                        e.target.src = "https://images.unsplash.com/photo-1550989460-0adf9ea622e2?auto=format&fit=crop&q=80&w=400";
                      }}
                    />
                  </div>
                  <div className="p-5 flex-1 flex flex-col justify-between">
                    <div>
                      <h3 className="font-bold text-gray-900 text-lg mb-1">{product.name}</h3>
                      <p className="text-sm text-gray-500 line-clamp-2 mb-4">{product.desc}</p>
                    </div>
                    <div className="flex items-center justify-between mt-auto">
                      <span className="text-xl font-black text-green-700">₹{cleanPrice(product.price)}</span>
                      <button onClick={() => addToCart(product)} className="bg-green-600 hover:bg-green-700 text-white font-bold px-4 py-2 rounded-lg transition-colors text-sm shadow-sm">
                        Add to Cart
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

      </main>

      {showCart && (
        <div className="fixed inset-0 z-50 flex justify-end bg-gray-900/60 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-md bg-white h-full shadow-2xl flex flex-col animate-slide-in-right">
            <div className="p-6 border-b border-gray-100 flex items-center justify-between bg-gray-50">
              <h2 className="text-2xl font-black text-gray-900 flex items-center">
                <ShoppingCart className="w-6 h-6 mr-3 text-green-600" /> Your Cart
              </h2>
              <button onClick={() => setShowCart(false)} className="text-gray-400 hover:text-gray-800"><X className="w-6 h-6" /></button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-6 space-y-4 custom-scrollbar">
              {cart.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-gray-400">
                  <ShoppingBag className="w-16 h-16 mb-4 opacity-50" />
                  <p>Your cart is empty.</p>
                </div>
              ) : (
                cart.map(item => (
                  <div key={item.id} className="flex items-center gap-4 bg-white p-4 rounded-xl border border-gray-100 shadow-sm">
                    <img 
                      src={item.image} 
                      alt={item.name} 
                      className="w-16 h-16 rounded-lg object-cover" 
                      onError={(e) => { e.target.onerror = null; e.target.src = "https://images.unsplash.com/photo-1550989460-0adf9ea622e2?auto=format&fit=crop&q=80&w=200"; }}
                    />
                    <div className="flex-1">
                      <h4 className="font-bold text-gray-900 text-sm">{item.name}</h4>
                      <p className="text-green-600 font-bold">₹{cleanPrice(item.price)}</p>
                    </div>
                    <div className="flex items-center space-x-2 bg-gray-50 border border-gray-200 rounded-lg p-1">
                      <button onClick={() => updateQty(item.id, -1)} className="p-1 text-gray-500 hover:text-red-500"><Minus className="w-4 h-4" /></button>
                      <span className="font-bold text-sm w-4 text-center">{item.qty}</span>
                      <button onClick={() => updateQty(item.id, 1)} className="p-1 text-gray-500 hover:text-green-600"><Plus className="w-4 h-4" /></button>
                    </div>
                  </div>
                ))
              )}
            </div>

            <div className="p-6 border-t border-gray-100 bg-gray-50">
              <div className="flex justify-between items-center mb-6">
                <span className="text-gray-600 font-medium">Subtotal</span>
                <span className="text-2xl font-black text-gray-900">₹{cartTotal}</span>
              </div>
              <button 
                disabled={cart.length === 0}
                onClick={handlePayment} 
                className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-300 text-white font-extrabold py-4 rounded-xl transition-all shadow-lg text-lg"
              >
                Proceed to Checkout
              </button>
            </div>
          </div>
        </div>
      )}

      {showProfile && user.ayurvedic_profile && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/60 backdrop-blur-sm p-4 animate-fade-in">
          <div className="bg-white rounded-3xl shadow-2xl w-full max-w-5xl max-h-[90vh] overflow-hidden flex flex-col relative">
            <button onClick={() => setShowProfile(false)} className="absolute top-4 right-4 z-10 bg-black/50 hover:bg-black/80 text-white p-2 rounded-full backdrop-blur-md transition-all">
              <X className="w-6 h-6" />
            </button>
            <div className="flex flex-col lg:flex-row h-full overflow-y-auto">
              
              <div className="lg:w-2/5 h-64 lg:h-auto relative shrink-0">
                <img 
                  src={
                    user.ayurvedic_profile.dosha.toLowerCase().includes('vata') 
                      ? "https://images.unsplash.com/photo-1545389336-eaee207e3713?auto=format&fit=crop&q=80&w=1000"
                    : user.ayurvedic_profile.dosha.toLowerCase().includes('pitta')
                      ? "https://images.unsplash.com/photo-1599901860904-17e6ed7083a0?auto=format&fit=crop&q=80&w=1000"
                    : "https://images.unsplash.com/photo-1575052814086-f385e2e2ad1b?auto=format&fit=crop&q=80&w=1000"
                  } 
                  alt="Yoga" className="absolute inset-0 w-full h-full object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-emerald-900/90 to-transparent flex items-end p-8">
                  <div>
                    <span className="bg-emerald-500/80 text-white text-xs font-bold uppercase px-3 py-1 rounded-full border border-emerald-400">AI Curated</span>
                    <h2 className="text-5xl font-black text-white mt-2">{user.ayurvedic_profile.dosha}</h2>
                  </div>
                </div>
              </div>

              <div className="lg:w-3/5 p-8 flex flex-col justify-center">
                <p className="text-gray-700 text-lg font-medium mb-6 italic border-l-4 border-emerald-500 pl-4 bg-emerald-50 py-3 pr-3 rounded-r-lg">
                  "{user.ayurvedic_profile.description}"
                </p>
                
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-6">
                  <div>
                    <h3 className="font-extrabold text-gray-900 flex items-center border-b pb-2 mb-3">
                      <CheckCircle2 className="w-5 h-5 mr-2 text-green-500"/> Favorable Diet
                    </h3>
                    <ul className="space-y-2">
                      {Array.isArray(user.ayurvedic_profile.diet_do) ? user.ayurvedic_profile.diet_do.map((item, i) => (
                        <li key={i} className="flex text-sm text-gray-700"><span className="text-green-500 mr-2">•</span> {item}</li>
                      )) : <li className="text-sm text-gray-700">{user.ayurvedic_profile.diet_do}</li>}
                    </ul>
                  </div>
                  <div>
                    <h3 className="font-extrabold text-gray-900 flex items-center border-b pb-2 mb-3">
                      <XCircle className="w-5 h-5 mr-2 text-red-500"/> Foods to Limit
                    </h3>
                    <ul className="space-y-2">
                      {Array.isArray(user.ayurvedic_profile.diet_dont) ? user.ayurvedic_profile.diet_dont.map((item, i) => (
                        <li key={i} className="flex text-sm text-gray-700"><span className="text-red-400 mr-2">•</span> {item}</li>
                      )) : <li className="text-sm text-gray-700">{user.ayurvedic_profile.diet_dont}</li>}
                    </ul>
                  </div>
                </div>

                <div className="bg-blue-50 p-5 rounded-xl border border-blue-100">
                  <h3 className="font-extrabold text-blue-900 flex items-center mb-3">
                    <Activity className="w-5 h-5 mr-2 text-blue-600"/> Recommended Yoga
                  </h3>
                  <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {Array.isArray(user.ayurvedic_profile.yoga) ? user.ayurvedic_profile.yoga.map((item, i) => (
                      <li key={i} className="flex items-center text-sm text-blue-900 font-bold bg-white px-3 py-2 rounded-lg shadow-sm border border-blue-100">
                        <Leaf className="w-4 h-4 mr-2 text-blue-500 shrink-0" /> {item}
                      </li>
                    )) : <p className="text-sm text-blue-800">{user.ayurvedic_profile.yoga}</p>}
                  </ul>
                </div>

              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}