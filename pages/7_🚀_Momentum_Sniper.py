import React, { useState, useMemo } from 'react';
import { 
  Target, 
  ShieldAlert, 
  Wallet, 
  LineChart, 
  MessageSquare, 
  Calculator,
  ChevronRight,
  PieChart,
  Settings,
  ArrowUpRight,
  TrendingUp,
  Activity,
  History,
  CheckCircle2,
  BarChart3,
  TrendingDown,
  AlertCircle
} from 'lucide-react';

const App = () => {
  // --- Dime! Fee Configuration ---
  const DIME_COMMISSION = 0.0015; // 0.15%
  const VAT = 0.07; // 7%
  const REGULATORY_FEE = 0.00007; // 0.007%

  // --- State Management ---
  const [activeTab, setActiveTab] = useState('scanner');
  const [cashBalance, setCashBalance] = useState(20172.03); // Initial + Today's Profit
  const [stock40k, setStock40k] = useState(40000);
  
  // Top 15 "Zing" Stocks based on 6 Strategic Sectors
  const [top15Stocks] = useState([
    { id: 1, symbol: 'WHA', sector: 'นิคมฯ', price: 4.12, change: 2.4, entry: 4.10, target: 4.30, stop: 4.02, status: 'Hot' },
    { id: 2, symbol: 'TRUE', sector: 'สื่อสาร', price: 12.30, change: 1.8, entry: 12.20, target: 13.00, stop: 11.90, status: 'Strong' },
    { id: 3, symbol: 'ADVANC', sector: 'สื่อสาร', price: 245, change: 0.5, entry: 242, target: 255, stop: 238, status: 'Steady' },
    { id: 4, symbol: 'SIRI', sector: 'อสังหาฯ', price: 1.82, change: 3.2, entry: 1.80, target: 1.95, stop: 1.76, status: 'Zing' },
    { id: 5, symbol: 'DOHOME', sector: 'ก่อสร้าง', price: 10.50, change: 4.1, entry: 10.40, target: 11.50, stop: 10.10, status: 'Breakout' },
    { id: 6, symbol: 'CPALL', sector: 'ค้าปลีก', price: 65.25, change: 1.2, entry: 64.50, target: 68.00, stop: 63.50, status: 'Steady' },
    { id: 7, symbol: 'AMATA', sector: 'นิคมฯ', price: 28.50, change: 2.1, entry: 28.00, target: 31.00, stop: 27.25, status: 'Strong' },
    { id: 8, symbol: 'AP', sector: 'อสังหาฯ', price: 10.80, change: 0.9, entry: 10.70, target: 11.50, stop: 10.40, status: 'Wait' },
    { id: 9, symbol: 'HANA', sector: 'เทค', price: 42.00, change: -1.5, entry: 41.50, target: 45.00, stop: 40.50, status: 'Rebound' },
    { id: 10, symbol: 'GLOBAL', sector: 'ก่อสร้าง', price: 16.80, change: 1.4, entry: 16.50, target: 18.20, stop: 16.10, status: 'Steady' },
    { id: 11, symbol: 'GULF', sector: 'เทค', price: 55.50, change: 0.7, entry: 54.00, target: 58.00, stop: 53.00, status: 'Steady' },
    { id: 12, symbol: 'CRC', sector: 'ค้าปลีก', price: 34.25, change: 2.8, entry: 33.75, target: 37.00, stop: 33.00, status: 'Strong' },
    { id: 13, symbol: 'SPALI', sector: 'อสังหาฯ', price: 19.80, change: -0.5, entry: 19.50, target: 21.00, stop: 19.20, status: 'Wait' },
    { id: 14, symbol: 'DELTA', sector: 'เทค', price: 152, change: 3.5, entry: 150, target: 165, stop: 145, status: 'Super Zing' },
    { id: 15, symbol: 'ROJNA', sector: 'นิคมฯ', price: 7.20, change: 1.1, entry: 7.10, target: 7.80, stop: 6.95, status: 'Steady' },
  ]);

  // Current Commander Portfolio (Core Stocks)
  const portfolio = [
    { symbol: 'TISCO', shares: 100, avgPrice: 112.50, currentPrice: 112.50, type: 'ออม' },
    { symbol: 'SCB', shares: 25, avgPrice: 135.50, currentPrice: 139.50, type: 'ออม' },
  ];

  // Helper: Calculate Dime! Fees (Buy or Sell)
  const calculateDimeFees = (price, shares) => {
    const grossValue = price * shares;
    const commission = grossValue * DIME_COMMISSION;
    const vatOnComm = commission * VAT;
    const regFee = grossValue * REGULATORY_FEE;
    return commission + vatOnComm + regFee;
  };

  const currentDailyProfit = 172.03;
  const totalPortfolioValue = useMemo(() => portfolio.reduce((acc, curr) => acc + (curr.shares * curr.currentPrice), 0), [portfolio]);

  // UI Components
  const StatusBadge = ({ status }) => {
    const styles = {
      'Super Zing': 'bg-rose-500/20 text-rose-500 border-rose-500/30',
      'Zing': 'bg-rose-400/20 text-rose-400 border-rose-400/30',
      'Hot': 'bg-amber-500/20 text-amber-500 border-amber-500/30',
      'Strong': 'bg-emerald-500/20 text-emerald-500 border-emerald-500/30',
      'Breakout': 'bg-blue-500/20 text-blue-500 border-blue-500/30',
      'Steady': 'bg-slate-800 text-slate-400 border-slate-700',
      'Wait': 'bg-slate-900 text-slate-600 border-slate-800',
      'Rebound': 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30'
    };
    return (
      <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase border ${styles[status] || styles['Steady']}`}>
        {status}
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 font-sans p-4 md:p-8">
      {/* Header Container */}
      <header className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-6">
        <div>
          <h1 className="text-3xl font-black tracking-tight text-white flex items-center gap-3">
            <Target className="text-blue-500" />
            SUCHAT PRO SNIPER
          </h1>
          <div className="flex items-center gap-2 mt-2">
            <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></div>
            <p className="text-[10px] text-slate-500 uppercase font-black tracking-widest">
              Dime! Integration • Engineering Edition v2.1
            </p>
          </div>
        </div>
        
        <div className="flex gap-3 w-full md:w-auto overflow-x-auto pb-2 md:pb-0">
          <div className="bg-slate-900 border border-slate-800 p-3 rounded-2xl flex items-center gap-4 min-w-[160px]">
            <Wallet className="text-blue-500" size={20} />
            <div>
              <p className="text-[9px] text-slate-500 font-bold uppercase">เงินในพอร์ต</p>
              <p className="text-lg font-mono text-white font-black">฿{cashBalance.toLocaleString()}</p>
            </div>
          </div>
          <div className="bg-slate-900 border border-slate-800 p-3 rounded-2xl flex items-center gap-4 min-w-[160px]">
            <PieChart className="text-amber-500" size={20} />
            <div>
              <p className="text-[9px] text-slate-500 font-bold uppercase">เงินสำรอง</p>
              <p className="text-lg font-mono text-white font-black">฿{stock40k.toLocaleString()}</p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Navigation */}
      <nav className="max-w-6xl mx-auto flex gap-1 mb-8 bg-slate-900/50 p-1 rounded-2xl border border-slate-800 sticky top-4 z-50 backdrop-blur-md">
        {[
          { id: 'scanner', label: 'Top 15 Sniper', icon: Target },
          { id: 'portfolio', label: 'พอร์ตแม่ทัพ', icon: ShieldAlert },
          { id: 'calculator', label: 'Dime! Calc', icon: Calculator },
          { id: 'history', label: 'ประวัติกำไร', icon: History },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-xl transition-all ${
              activeTab === tab.id 
              ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/40 font-bold' 
              : 'text-slate-500 hover:bg-slate-800 hover:text-slate-300'
            }`}
          >
            <tab.icon size={18} />
            <span className="hidden md:inline text-xs uppercase tracking-wider">{tab.label}</span>
          </button>
        ))}
      </nav>

      <main className="max-w-6xl mx-auto">
        {/* TAB: SCANNER */}
        {activeTab === 'scanner' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
               <div className="bg-slate-900 border border-slate-800 p-4 rounded-2xl">
                 <p className="text-[10px] text-slate-500 font-bold uppercase mb-1">กลุ่มเป้าหมาย</p>
                 <div className="flex flex-wrap gap-1">
                   {['TECH', 'ICT', 'PROP', 'CON', 'COMM', 'IE'].map(s => (
                     <span key={s} className="bg-blue-500/10 text-blue-400 px-2 py-0.5 rounded text-[9px] font-black border border-blue-500/20">{s}</span>
                   ))}
                 </div>
               </div>
               <div className="bg-emerald-900/20 border border-emerald-500/20 p-4 rounded-2xl flex justify-between items-center">
                 <div>
                   <p className="text-[10px] text-emerald-500 font-bold uppercase mb-1">กำไรวันนี้ (NET)</p>
                   <p className="text-xl font-mono font-black text-white">฿{currentDailyProfit.toLocaleString()}</p>
                 </div>
                 <ArrowUpRight className="text-emerald-500" />
               </div>
               <div className="bg-slate-900 border border-slate-800 p-4 rounded-2xl flex justify-between items-center">
                 <div>
                   <p className="text-[10px] text-slate-500 font-bold uppercase mb-1">ความแม่นยำ</p>
                   <p className="text-xl font-mono font-black text-white">78.5%</p>
                 </div>
                 <Activity className="text-blue-500" />
               </div>
               <div className="bg-slate-900 border border-slate-800 p-4 rounded-2xl flex justify-between items-center cursor-pointer hover:bg-slate-800">
                 <div>
                   <p className="text-[10px] text-blue-500 font-bold uppercase mb-1">LINE REPORT</p>
                   <p className="text-xl font-mono font-black text-white">3165</p>
                 </div>
                 <MessageSquare className="text-blue-500" />
               </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-3xl overflow-hidden">
              <div className="p-6 border-b border-slate-800 flex justify-between items-center bg-slate-900/30">
                <h3 className="font-black text-lg text-white flex items-center gap-2">
                  <BarChart3 size={20} className="text-blue-500" />
                  TOP 15 STRATEGIC SNIPER WATCHLIST
                </h3>
                <div className="flex items-center gap-2">
                   <span className="text-[9px] bg-slate-800 text-slate-500 px-3 py-1 rounded-full font-bold">13 FEB 2026</span>
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead>
                    <tr className="bg-slate-950/50 text-slate-500 text-[9px] uppercase tracking-[0.2em] font-black">
                      <th className="px-6 py-4">SYMBOL / SECTOR</th>
                      <th className="px-4 py-4">PRICE / CHANGE</th>
                      <th className="px-4 py-4 text-amber-500">ENTRY (จุดเข้า)</th>
                      <th className="px-4 py-4 text-emerald-500">TARGET (เป้า)</th>
                      <th className="px-4 py-4 text-rose-500">STOP (คัด)</th>
                      <th className="px-4 py-4 text-center">STATUS</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {top15Stocks.map((stock) => (
                      <tr key={stock.id} className="hover:bg-blue-500/5 transition-colors group">
                        <td className="px-6 py-4">
                          <div className="font-black text-white group-hover:text-blue-400">{stock.symbol}</div>
                          <div className="text-[9px] font-bold text-slate-600 uppercase">{stock.sector}</div>
                        </td>
                        <td className="px-4 py-4 font-mono">
                          <div className="text-slate-300 font-bold">{stock.price.toFixed(2)}</div>
                          <div className={`text-[10px] font-bold ${stock.change >= 0 ? 'text-emerald-500' : 'text-rose-500'}`}>
                            {stock.change >= 0 ? '▲' : '▼'} {Math.abs(stock.change)}%
                          </div>
                        </td>
                        <td className="px-4 py-4 font-mono text-amber-500 font-black text-lg">{stock.entry.toFixed(2)}</td>
                        <td className="px-4 py-4 font-mono text-emerald-500 font-black text-lg">{stock.target.toFixed(2)}</td>
                        <td className="px-4 py-4 font-mono text-rose-500 font-black text-lg">{stock.stop.toFixed(2)}</td>
                        <td className="px-4 py-4 text-center">
                          <StatusBadge status={stock.status} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* TAB: PORTFOLIO */}
        {activeTab === 'portfolio' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6">
                <h3 className="text-xl font-black mb-6 flex items-center gap-2">
                  <ShieldAlert className="text-emerald-500" />
                  COMMANDER CORE (หุ้นเสาเข็ม)
                </h3>
                <div className="space-y-3">
                  {portfolio.map(stock => (
                    <div key={stock.symbol} className="bg-slate-950 p-5 rounded-2xl border border-slate-800 flex justify-between items-center">
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="font-black text-xl text-white">{stock.symbol}</p>
                          <span className="text-[9px] bg-slate-800 text-slate-500 px-2 py-0.5 rounded font-bold uppercase">{stock.type}</span>
                        </div>
                        <p className="text-xs text-slate-500 font-mono mt-1">{stock.shares} หุ้น @ {stock.avgPrice.toFixed(2)}</p>
                      </div>
                      <div className="text-right">
                        <p className="font-mono text-xl font-black text-white">฿{(stock.shares * stock.currentPrice).toLocaleString()}</p>
                        <p className={`text-xs font-bold mt-1 ${stock.currentPrice >= stock.avgPrice ? 'text-emerald-500' : 'text-rose-500'}`}>
                           {stock.currentPrice >= stock.avgPrice ? '+' : ''}
                           {((stock.currentPrice - stock.avgPrice) / stock.avgPrice * 100).toFixed(2)}%
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6">
                 <div className="flex justify-between items-center mb-6">
                   <h3 className="text-xl font-black flex items-center gap-2 text-blue-500">
                     <TrendingUp size={24} />
                     ASSET ALLOCATION
                   </h3>
                   <p className="text-xs font-bold text-slate-500 uppercase tracking-widest">Dime! Portfolio</p>
                 </div>
                 <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 bg-slate-950 rounded-2xl border border-slate-800">
                      <p className="text-[10px] text-slate-500 font-black uppercase mb-1">MKT Value</p>
                      <p className="text-2xl font-mono font-black text-white">฿{totalPortfolioValue.toLocaleString()}</p>
                    </div>
                    <div className="p-4 bg-slate-950 rounded-2xl border border-slate-800">
                      <p className="text-[10px] text-slate-500 font-black uppercase mb-1">Total Cash</p>
                      <p className="text-2xl font-mono font-black text-emerald-500">฿{(cashBalance + stock40k).toLocaleString()}</p>
                    </div>
                 </div>
              </div>
            </div>

            <div className="space-y-6">
               <div className="bg-slate-900 border border-slate-800 rounded-3xl p-8 flex flex-col items-center text-center">
                 <div className="h-20 w-20 rounded-2xl bg-blue-500/10 flex items-center justify-center border border-blue-500/20 mb-6">
                   <PieChart size={36} className="text-blue-500" />
                 </div>
                 <h4 className="text-xl font-black uppercase mb-2">บทวิเคราะห์วิศวกร</h4>
                 <p className="text-slate-500 text-sm leading-relaxed mb-6">
                   พี่โบ้ครับ! สัดส่วนพอร์ตตอนนี้ "เสาเข็มปันผล" 75% และ "กระสุนซิ่ง" 25% มั่นคงแต่ยังทำรอบได้ เหมาะสำหรับสะสมเงินทุนขอหลักแสนครับ
                 </p>
                 <button className="w-full py-4 bg-blue-600 hover:bg-blue-500 text-white rounded-2xl font-black uppercase tracking-widest transition-all shadow-lg shadow-blue-900/20">
                   เติมเงินจากสต็อก
                 </button>
               </div>
            </div>
          </div>
        )}

        {/* TAB: CALCULATOR */}
        {activeTab === 'calculator' && (
          <div className="max-w-2xl mx-auto bg-slate-900 border border-slate-800 rounded-3xl p-8">
            <h3 className="text-2xl font-black mb-8 flex items-center gap-3">
              <Calculator className="text-amber-500" size={28} />
              DIME! NET CALCULATOR
            </h3>
            <div className="grid grid-cols-2 gap-6 mb-8">
              <div className="col-span-2">
                <label className="block text-[10px] text-slate-500 mb-2 uppercase font-black">ชื่อหุ้นเป้าหมาย</label>
                <input type="text" placeholder="WHA" className="w-full bg-slate-950 border border-slate-800 p-4 rounded-2xl focus:border-blue-500 outline-none font-bold" />
              </div>
              <div>
                <label className="block text-[10px] text-amber-500 mb-2 uppercase font-black">ราคาซื้อ (Buy)</label>
                <input type="number" defaultValue={3.88} step="0.01" className="w-full bg-slate-950 border border-amber-500/20 p-4 rounded-2xl focus:border-amber-500 outline-none font-bold font-mono text-amber-400" />
              </div>
              <div>
                <label className="block text-[10px] text-emerald-500 mb-2 uppercase font-black">ราคาขาย (Sell)</label>
                <input type="number" defaultValue={4.00} step="0.01" className="w-full bg-slate-950 border border-emerald-500/20 p-4 rounded-2xl focus:border-emerald-500 outline-none font-bold font-mono text-emerald-400" />
              </div>
            </div>

            <div className="bg-slate-950 rounded-3xl p-8 border border-slate-800">
               <div className="flex justify-between items-center mb-4">
                 <span className="text-slate-500 font-bold">ยอดกำไรก่อนหักค่าธรรมเนียม</span>
                 <span className="font-mono text-white text-xl">฿60.00</span>
               </div>
               <div className="flex justify-between items-center mb-6 text-rose-500 font-bold italic text-sm">
                 <span>Dime! Fee (0.15% + VAT + Reg)</span>
                 <span className="font-mono">-฿12.45</span>
               </div>
               <div className="pt-6 border-t border-slate-800 flex justify-between items-end">
                  <div>
                    <span className="text-[10px] text-slate-500 font-black uppercase tracking-[0.2em] block mb-1">กำไรเข้ากระเป๋าสุทธิ (NET)</span>
                    <span className="text-5xl font-black text-emerald-500 font-mono italic">฿47.55</span>
                  </div>
                  <ArrowUpRight size={48} className="text-emerald-500/20" />
               </div>
            </div>
            <p className="text-center text-[9px] text-slate-600 mt-6 font-bold uppercase tracking-widest">สูตรคำนวณ Dime! Precision 100%</p>
          </div>
        )}

        {/* TAB: HISTORY */}
        {activeTab === 'history' && (
          <div className="max-w-2xl mx-auto space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-8">
              <h3 className="text-2xl font-black mb-6 flex items-center gap-3">
                <History className="text-blue-500" />
                PROFIT HISTORY (บันทึกชัยชนะ)
              </h3>
              <div className="space-y-4">
                <div className="bg-slate-950 p-5 rounded-2xl border-l-4 border-l-emerald-500 flex justify-between items-center shadow-lg">
                   <div>
                     <p className="font-black text-white text-lg">GPSC + WHA (Zing Run)</p>
                     <p className="text-[10px] text-slate-600 font-bold">12 FEB 2026 • ปิดจ๊อบสำเร็จ</p>
                   </div>
                   <div className="text-right">
                     <p className="text-2xl font-mono font-black text-emerald-500">+฿172.03</p>
                     <p className="text-[9px] text-slate-600 font-bold uppercase">Net After Fee</p>
                   </div>
                </div>
                
                <div className="bg-slate-950 p-5 rounded-2xl border-l-4 border-l-slate-800 opacity-40 italic flex justify-between items-center">
                   <div>
                     <p className="font-black text-slate-500">Upcoming Profit...</p>
                     <p className="text-[10px] text-slate-700">รอจังหวะยิง Sniper</p>
                   </div>
                   <p className="text-xl font-mono font-black text-slate-700">฿300.00</p>
                </div>
              </div>

              <div className="mt-8 p-8 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-3xl text-white shadow-xl relative overflow-hidden group">
                 <div className="relative z-10">
                   <p className="text-[10px] font-black uppercase tracking-widest mb-1 text-blue-100">กำไรสะสมประจำเดือนกุมภาพันธ์</p>
                   <div className="flex justify-between items-end">
                      <p className="text-5xl font-black font-mono italic">฿172.03</p>
                      <BarChart3 size={40} className="opacity-40" />
                   </div>
                 </div>
                 <div className="absolute -bottom-4 -right-4 h-24 w-24 bg-white/10 rounded-full blur-2xl group-hover:scale-150 transition-transform"></div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* FOOTER */}
      <footer className="max-w-6xl mx-auto mt-20 pb-12 border-t border-slate-900 pt-10 flex flex-col md:flex-row justify-between items-center text-slate-600 text-[9px] font-black uppercase tracking-[0.2em] gap-8">
        <p>© 2026 SUCHAT ENGINEERING TRADING SYSTEM • EXCLUSIVELY FOR P'BO</p>
        <div className="flex gap-8">
          <span className="flex items-center gap-2 text-blue-500"><Target size={14}/> SYSTEM READY</span>
          <span className="flex items-center gap-2 text-emerald-500"><MessageSquare size={14}/> 3165: CONNECTED</span>
        </div>
      </footer>

      <style jsx>{`
        .no-scrollbar::-webkit-scrollbar { display: none; }
        .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
      `}</style>
    </div>
  );
};

export default App;
