import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, Lock, Activity, ArrowRight, Leaf } from 'lucide-react';

export default function Auth() {
  const [isLogin, setIsLogin] = useState(true);
  
  const [formData, setFormData] = useState({
    name: '', password: '', age: '', weight: '', height: '', gender: 'Male',
    digestion: 'Balanced', sleep: 'Deep & Heavy', weather: 'Tolerant', frame: 'Athletic / Medium'
  });
  
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(''); setLoading(true);
    try {
      if (!isLogin) {
        const response = await fetch("http://localhost:8000/register", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            ...formData, age: parseInt(formData.age), weight: parseFloat(formData.weight), height: parseFloat(formData.height)
          }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Registration failed");
        alert('Registration Successful! Please log in.');
        setIsLogin(true); 
      } else {
        const response = await fetch("http://localhost:8000/login", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name: formData.name, password: formData.password }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Login failed");
        localStorage.setItem('currentUser', JSON.stringify(data.user));
        navigate('/dashboard');
      }
    } catch (err) { setError(err.message); } 
    finally { setLoading(false); }
  };

  const inputStyle = "w-full mt-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:outline-none bg-white text-gray-900 text-sm";
  const labelStyle = "text-xs font-bold text-gray-500 uppercase tracking-wider";

  return (
    <div className="flex w-full h-screen bg-gray-50 overflow-hidden">
      
      {/* LEFT SIDE: Image (Hidden on small screens) */}
      <div className="hidden lg:flex lg:w-1/2 relative h-full">
        <img 
          src="https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?auto=format&fit=crop&q=80&w=1200" 
          alt="Medical Facility" 
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-green-900/90 to-transparent flex flex-col justify-end p-12">
          <Leaf className="w-10 h-10 text-green-300 mb-4" />
          <h1 className="text-5xl font-black text-white mb-2 leading-tight">Intelligent Diagnosis.</h1>
          <p className="text-green-50 text-lg max-w-md font-medium">Predict diseases and receive Ayurvedic medicinal protocols instantly based on your symptoms.</p>
        </div>
      </div>

      {/* RIGHT SIDE: Form Container */}
      <div className="w-full lg:w-1/2 h-full flex flex-col items-center justify-center p-6">
        <div className="w-full max-w-md bg-white p-8 rounded-2xl shadow-xl border border-gray-100 flex flex-col justify-center max-h-[95vh] overflow-y-auto custom-scrollbar">
          
          <div className="text-center mb-6">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Activity className="w-8 h-8 text-green-600" />
            </div>
            <h2 className="text-3xl font-extrabold text-gray-900">
              {isLogin ? 'Welcome Back' : 'Patient Registration'}
            </h2>
          </div>

          {error && <div className="mb-4 p-3 bg-red-50 text-red-600 text-sm font-bold rounded-lg text-center">{error}</div>}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className={isLogin ? "col-span-2" : "col-span-2 md:col-span-1"}>
                <label className={labelStyle}>Username</label>
                <div className="relative">
                  <User className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
                  <input type="text" name="name" required value={formData.name} onChange={handleChange} className={`pl-10 ${inputStyle}`} placeholder="Username"/>
                </div>
              </div>

              <div className={isLogin ? "col-span-2" : "col-span-2 md:col-span-1"}>
                <label className={labelStyle}>Password</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
                  <input type="password" name="password" required value={formData.password} onChange={handleChange} className={`pl-10 ${inputStyle}`} placeholder="Password"/>
                </div>
              </div>
            </div>

            {!isLogin && (
              <>
                <div className="grid grid-cols-4 gap-2 border-t border-gray-100 pt-3">
                  <div className="col-span-1"><label className={labelStyle}>Age</label><input type="number" name="age" required value={formData.age} onChange={handleChange} className={inputStyle} /></div>
                  <div className="col-span-1"><label className={labelStyle}>Gen</label><select name="gender" value={formData.gender} onChange={handleChange} className={inputStyle}><option>Male</option><option>Female</option></select></div>
                  <div className="col-span-1"><label className={labelStyle}>Wt</label><input type="number" step="0.1" name="weight" required value={formData.weight} onChange={handleChange} className={inputStyle} /></div>
                  <div className="col-span-1"><label className={labelStyle}>Ht</label><input type="number" step="0.1" name="height" required value={formData.height} onChange={handleChange} className={inputStyle} /></div>
                </div>

                <div className="grid grid-cols-2 gap-3 border-t border-gray-100 pt-3">
                  <div><label className={labelStyle}>Digestion</label><select name="digestion" value={formData.digestion} onChange={handleChange} className={inputStyle}><option>Balanced</option><option>Fast</option><option>Slow</option><option>Irregular</option></select></div>
                  <div><label className={labelStyle}>Sleep</label><select name="sleep" value={formData.sleep} onChange={handleChange} className={inputStyle}><option>Deep</option><option>Light</option><option>Moderate</option><option>Interrupted</option></select></div>
                  <div><label className={labelStyle}>Weather</label><select name="weather" value={formData.weather} onChange={handleChange} className={inputStyle}><option>Tolerant</option><option>Always Cold</option><option>Always Hot</option></select></div>
                  <div><label className={labelStyle}>Frame</label><select name="frame" value={formData.frame} onChange={handleChange} className={inputStyle}><option>Medium</option><option>Thin</option><option>Broad</option></select></div>
                </div>
              </>
            )}

            <button type="submit" disabled={loading} className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 rounded-xl transition-all flex justify-center items-center shadow-md disabled:bg-gray-400 mt-2">
              {loading ? <Activity className="animate-spin w-5 h-5" /> : (isLogin ? 'Sign In' : 'Register Account')} 
              {!loading && <ArrowRight className="ml-2 w-5 h-5" />}
            </button>
          </form>

          <p className="mt-5 text-center text-sm text-gray-600 font-medium">
            {isLogin ? "New patient? " : "Already registered? "}
            <button onClick={() => setIsLogin(!isLogin)} className="text-green-600 font-extrabold hover:underline">
              {isLogin ? 'Sign up' : 'Log in'}
            </button>
          </p>

        </div>
      </div>
    </div>
  );
}