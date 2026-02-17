import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldAlert, ListOrdered, Activity, LogOut, Package } from 'lucide-react';

export default function Admin() {
  const [activeTab, setActiveTab] = useState("orders");
  const [orders, setOrders] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    // In a real app, you'd check if the user is an Admin here. 
    // For your presentation, we just load the data.
    const fetchData = async () => {
      setLoading(true);
      try {
        const [ordersRes, logsRes] = await Promise.all([
          fetch("http://localhost:8000/admin/orders"),
          fetch("http://localhost:8000/admin/logs")
        ]);
        
        const ordersData = await ordersRes.json();
        const logsData = await logsRes.json();
        
        setOrders(ordersData.orders || []);
        setLogs(logsData.logs || []);
      } catch (err) {
        console.error("Failed to fetch admin data", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  return (
    <div className="flex h-screen bg-gray-100 font-sans">
      
      {/* SIDEBAR */}
      <div className="w-64 bg-slate-900 text-white flex flex-col shadow-2xl z-10">
        <div className="p-6 border-b border-slate-800 flex items-center space-x-3">
          <ShieldAlert className="w-8 h-8 text-emerald-400" />
          <h1 className="text-xl font-black tracking-wider">SYSTEM<br/><span className="text-emerald-400">ADMIN</span></h1>
        </div>
        
        <div className="flex-1 py-6 flex flex-col gap-2 px-4">
          <button 
            onClick={() => setActiveTab("orders")}
            className={`flex items-center space-x-3 w-full p-3 rounded-lg transition-all font-bold ${activeTab === "orders" ? "bg-emerald-500 text-white" : "text-slate-400 hover:bg-slate-800 hover:text-white"}`}
          >
            <ListOrdered className="w-5 h-5" /> <span>E-Commerce Orders</span>
          </button>
          <button 
            onClick={() => setActiveTab("logs")}
            className={`flex items-center space-x-3 w-full p-3 rounded-lg transition-all font-bold ${activeTab === "logs" ? "bg-emerald-500 text-white" : "text-slate-400 hover:bg-slate-800 hover:text-white"}`}
          >
            <Activity className="w-5 h-5" /> <span>Diagnosis Logs</span>
          </button>
        </div>

        <div className="p-4 border-t border-slate-800">
          <button onClick={() => navigate('/dashboard')} className="flex items-center justify-center space-x-2 w-full p-3 bg-slate-800 hover:bg-red-500 text-white rounded-lg transition-colors font-bold text-sm">
            <LogOut className="w-4 h-4" /> <span>Exit Admin</span>
          </button>
        </div>
      </div>

      {/* MAIN CONTENT */}
      <div className="flex-1 overflow-y-auto p-10 bg-slate-50">
        <div className="mb-8">
          <h2 className="text-3xl font-black text-slate-800">
            {activeTab === "orders" ? "Sales & Orders Hub" : "AI Diagnostic Tracking"}
          </h2>
          <p className="text-slate-500 mt-1 font-medium">
            {activeTab === "orders" ? "Monitor your pharmacy revenue and recent customer transactions." : "Audit trail of patient symptoms and AI model predictions."}
          </p>
        </div>

        {loading ? (
          <div className="flex justify-center items-center h-64"><Activity className="w-10 h-10 text-emerald-500 animate-spin" /></div>
        ) : (
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
            
            {/* ORDERS TABLE */}
            {activeTab === "orders" && (
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-100 border-b border-slate-200 text-slate-600 text-sm uppercase tracking-wider">
                    <th className="p-4 font-black">Order ID</th>
                    <th className="p-4 font-black">Customer</th>
                    <th className="p-4 font-black">Amount</th>
                    <th className="p-4 font-black">Items</th>
                    <th className="p-4 font-black">Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {orders.length === 0 ? (
                    <tr><td colSpan="5" className="p-8 text-center text-slate-400 font-medium">No orders found.</td></tr>
                  ) : (
                    orders.map((o, i) => (
                      <tr key={i} className="hover:bg-slate-50 transition-colors">
                        <td className="p-4 font-mono text-xs font-bold text-slate-500">{o.payment_id}</td>
                        <td className="p-4 font-bold text-slate-800">{o.username}</td>
                        <td className="p-4 font-black text-emerald-600">₹{o.amount_paid}</td>
                        <td className="p-4">
                          <div className="flex flex-col gap-1">
                            {o.items.map((item, idx) => (
                              <span key={idx} className="text-xs font-bold bg-slate-100 text-slate-600 px-2 py-1 rounded inline-flex items-center w-max">
                                <Package className="w-3 h-3 mr-1"/> {item.name} (x{item.qty})
                              </span>
                            ))}
                          </div>
                        </td>
                        <td className="p-4 text-sm text-slate-500 font-medium">{o.timestamp}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            )}

            {/* LOGS TABLE */}
            {activeTab === "logs" && (
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-100 border-b border-slate-200 text-slate-600 text-sm uppercase tracking-wider">
                    <th className="p-4 font-black">Patient</th>
                    <th className="p-4 font-black w-1/3">Symptoms Described</th>
                    <th className="p-4 font-black">AI Prediction</th>
                    <th className="p-4 font-black">Confidence</th>
                    <th className="p-4 font-black">Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {logs.length === 0 ? (
                    <tr><td colSpan="5" className="p-8 text-center text-slate-400 font-medium">No diagnostic logs found.</td></tr>
                  ) : (
                    logs.map((log, i) => (
                      <tr key={i} className="hover:bg-slate-50 transition-colors">
                        <td className="p-4 font-bold text-slate-800">{log.username}</td>
                        <td className="p-4 text-sm text-slate-600 italic">"{log.symptoms}"</td>
                        <td className="p-4">
                          <span className={`text-xs font-black px-3 py-1 rounded-full ${log.predicted_disease === 'Unknown' || log.predicted_disease === 'Blocked by Guardrail' ? 'bg-red-100 text-red-700' : 'bg-blue-100 text-blue-700'}`}>
                            {log.predicted_disease}
                          </span>
                        </td>
                        <td className="p-4 font-black text-slate-700">{log.confidence}%</td>
                        <td className="p-4 text-sm text-slate-500 font-medium">{log.timestamp}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            )}

          </div>
        )}
      </div>
    </div>
  );
}