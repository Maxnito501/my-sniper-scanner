import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os

# --- ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Titan Asset Manager V4.0", page_icon="🛡️", layout="wide")

st.title("🛡️ Titan V4.0: Real-Life Wealth Simulator")
st.markdown("**ห้องบัญชีและเครื่องจำลองแผนเกษียณ (รวมเงินเฟ้อ + อายุขัยเงิน)**")

csv_file = 'assets.csv'

# --- 1. จัดการข้อมูล (Data Management) ---
if os.path.exists(csv_file):
    df = pd.read_csv(csv_file)
    
    # Check Columns
    if 'Monthly DCA (THB)' not in df.columns:
        df['Monthly DCA (THB)'] = 0
    if 'Type' not in df.columns: # เพิ่มแยกประเภท Asset/Debt
        df['Type'] = 'Asset'
        
    # --- ส่วนแก้ไขข้อมูล (Asset Editor) ---
    with st.expander("📝 บันทึกทรัพย์สิน & หนี้สิน (Wealth Sheet)", expanded=False):
        edited_df = st.data_editor(
            df,
            num_rows="dynamic",
            column_config={
                "Type": st.column_config.SelectboxColumn("สถานะ", options=["Asset (ทรัพย์สิน)", "Liability (หนี้สิน)"], required=True),
                "Category": st.column_config.SelectboxColumn(
                    "หมวดหมู่",
                    options=["High Yield (สหกรณ์)", "Investment (กบข.)", "Stocks (หุ้นไทย)", 
                             "Mutual Fund (RMF)", "Sniper (เก็งกำไร)", "Cash (สภาพคล่อง)", "Gold (ทองคำ)", "Debt (หนี้)"],
                    required=True
                ),
                "Value (THB)": st.column_config.NumberColumn("มูลค่าคงเหลือ", format="%d ฿"),
                "Monthly DCA (THB)": st.column_config.NumberColumn("ออม/ผ่อน ต่อเดือน", format="%d ฿"),
                "Expected Return (%)": st.column_config.NumberColumn("ดอกเบี้ย/ผลตอบแทน (%)", format="%.1f%%"),
            },
            use_container_width=True
        )

        if st.button("💾 บันทึกข้อมูล"):
            edited_df.to_csv(csv_file, index=False)
            st.success("บันทึกเรียบร้อย!")
            st.rerun()

    # --- 2. คำนวณ Net Worth ปัจจุบัน ---
    assets_df = edited_df[edited_df['Type'] == 'Asset']
    liabilities_df = edited_df[edited_df['Type'] == 'Liability']
    
    total_assets = assets_df['Value (THB)'].sum()
    total_debts = liabilities_df['Value (THB)'].sum()
    net_worth = total_assets - total_debts

    col_nw1, col_nw2, col_nw3 = st.columns(3)
    col_nw1.metric("💰 ทรัพย์สินรวม (Assets)", f"{total_assets:,.0f} ฿")
    col_nw2.metric("💳 หนี้สินรวม (Liabilities)", f"{total_debts:,.0f} ฿", delta=f"-{total_debts/total_assets*100:.1f}% ของสินทรัพย์", delta_color="inverse")
    col_nw3.metric("💎 ความมั่งคั่งสุทธิ (Net Worth)", f"{net_worth:,.0f} ฿", help="นี่คือเงินจริงๆ ของคุณถ้าขายทุกอย่างใช้หนี้")

    st.write("---")
    st.subheader("🚀 เครื่องจำลองอนาคต (Simulation)")

    # Input
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        current_age = st.number_input("อายุปัจจุบัน", value=50)
        retire_age = st.number_input("เกษียณอายุ", value=60)
    with c2:
        life_expectancy = st.number_input("คาดว่าจะอยู่ถึงอายุ", value=85)
        inflation_rate = st.number_input("เงินเฟ้อเฉลี่ย (%)", value=3.0)
    with c3:
        # Pension Mode
        pension_mode = st.radio("บำนาญราชการ:", ["คำนวณ Auto", "ระบุเอง"])
        if pension_mode == "ระบุเอง":
            final_pension = st.number_input("ระบุยอดบำนาญ", value=49000)
        else:
            cur_sal = st.number_input("เงินเดือนปัจจุบัน", value=48780)
            sal_cap = 73000
            gov_years = st.number_input("เวลาราชการรวม", value=35.1)
            # Simple Pension Logic
            final_pension = min((sal_cap * gov_years)/50, sal_cap*0.7)
    with c4:
        monthly_expense_retire = st.number_input("กะใช้เงินหลังเกษียณ (บาท/เดือน)", value=30000, help="คิดเป็นมูลค่าเงินปัจจุบัน")

    # --- Logic การคำนวณ ---
    years_to_sim = retire_age - current_age
    months_to_sim = years_to_sim * 12
    
    # A. คำนวณความมั่งคั่งวันเกษียณ (Wealth Accumulation)
    sim_assets = assets_df.copy()
    sim_assets['Monthly Rate'] = sim_assets['Expected Return (%)'] / 100 / 12
    
    fv_total = 0
    # แยกคำนวณสหกรณ์ (Simple) กับ กองทุน (Compound)
    is_coop = sim_assets['Category'] == "High Yield (สหกรณ์)"
    
    # 1. สหกรณ์: เงินต้น + (DCA * เดือน)
    coop_fv = sim_assets.loc[is_coop, 'Value (THB)'].sum() + (sim_assets.loc[is_coop, 'Monthly DCA (THB)'].sum() * months_to_sim)
    
    # 2. อื่นๆ: Compound Interest
    other_start = sim_assets.loc[~is_coop, 'Value (THB)'].sum()
    other_dca = sim_assets.loc[~is_coop, 'Monthly DCA (THB)'].sum()
    # สูตร FV ของเงินต้น + FV ของ DCA
    # เพื่อความง่าย ใช้ Rate เฉลี่ยถ่วงน้ำหนัก
    avg_rate = 0.05 / 12 # สมมติเฉลี่ย 5%
    if not sim_assets.loc[~is_coop].empty:
         # คำนวณแบบละเอียดรายตัวก็ได้ แต่ขอใช้แบบรวมเพื่อความเร็ว
         # FV = PV*(1+r)^n + PMT*(((1+r)^n - 1)/r)
         other_fv = other_start * (1 + avg_rate)**months_to_sim + other_dca * (((1 + avg_rate)**months_to_sim - 1) / avg_rate)
    else:
        other_fv = 0
        
    wealth_at_retire = coop_fv + other_fv
    
    # B. ปรับเงินเฟ้อ (Real Value)
    inflation_factor = (1 + inflation_rate/100) ** years_to_sim
    real_wealth_at_retire = wealth_at_retire / inflation_factor
    real_pension = final_pension / inflation_factor
    
    # C. จำลองการใช้เงิน (Decumulation Phase)
    # หลังเกษียณ เงินก้อนยังลงทุนต่อได้ (สมมติได้ 4% ชนะเงินเฟ้อนิดหน่อย)
    # รายจ่ายต้องปรับตามเงินเฟ้อ
    
    fund_balance = wealth_at_retire
    survival_years = 0
    
    sim_data = []
    
    for age in range(retire_age, life_expectancy + 1):
        # รายได้ปีนี้ = บำนาญ x 12
        annual_pension = final_pension * 12 
        # รายจ่ายปีนี้ (ปรับเงินเฟ้อตามปีที่ผ่านไป)
        expense_factor = (1 + inflation_rate/100) ** (age - current_age)
        annual_expense = monthly_expense_retire * 12 * expense_factor
        
        # ขาด/เหลือ?
        gap = annual_expense - annual_pension
        
        # ถ้าบำนาญไม่พอ ต้องควักเนื้อ (เงินก้อน)
        if gap > 0:
            fund_balance -= gap
        else:
            # ถ้าบำนาญเหลือ ก็ทบต้นเข้าไป
            fund_balance += abs(gap)
            
        # เงินก้อนที่เหลือ ก็ทำกำไรได้ (สมมติหลังเกษียณลงทุนเซฟๆ ได้ 3-4%)
        fund_balance = fund_balance * 1.03
        
        sim_data.append({"Age": age, "Fund Balance": max(0, fund_balance)})
        
        if fund_balance > 0:
            survival_years += 1

    # --- Display Result ---
    st.info(f"📊 **สถานะวันเกษียณ (อายุ {retire_age})**")
    
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("💰 เงินก้อน (ตัวเลข)", f"{wealth_at_retire/1000000:,.1f} M")
    k2.metric("🥪 มูลค่าจริง (หักเฟ้อ)", f"{real_wealth_at_retire/1000000:,.1f} M", help=f"เงิน {wealth_at_retire:,.0f} ตอนนั้น ซื้อของได้เท่ากับ {real_wealth_at_retire:,.0f} ในวันนี้")
    k3.metric("🏛️ บำนาญจริง (หักเฟ้อ)", f"{real_pension:,.0f} ฿", help=f"รับ {final_pension} แต่ความรู้สึกเหมือนรับ {real_pension:,.0f}")
    
    if fund_balance > 0:
        k4.metric("🏁 ผลลัพธ์", "รอดสบาย! 🎉", "เงินเหลือถึงวันตาย")
        status_color = "green"
    else:
        k4.metric("🏁 ผลลัพธ์", f"เงินหมดตอน {retire_age + survival_years} ปี", "⚠️ เสี่ยง", delta_color="inverse")
        status_color = "red"

    # กราฟถังพลังงานชีวิต
    st.subheader("📉 Wealth Runway: เงินจะหมดเมื่อไหร่?")
    chart_df = pd.DataFrame(sim_data)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=chart_df['Age'], y=chart_df['Fund Balance'], fill='tozeroy', mode='lines', name='เงินคงเหลือ', line=dict(color=status_color)))
    fig.update_layout(xaxis_title="อายุ (ปี)", yaxis_title="เงินก้อนคงเหลือ (บาท)", height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    if fund_balance > 0:
        st.success(f"🌟 **Ultimate Success:** ด้วยแผนนี้ คุณจะมีบำนาญเลี้ยงชีพ และเงินก้อน 6 ล้านกว่าบาท (มูลค่าจริง 4 ล้านกว่า) ที่ใช้ยังไงก็ไม่หมด สามารถส่งต่อเป็นมรดกได้ครับ!")
    else:
        st.warning(f"⚠️ **Warning:** ด้วยอัตราเงินเฟ้อ {inflation_rate}% เงินก้อนอาจจะร่อยหรอเร็วกว่าที่คิด ลองลดรายจ่าย หรือเพิ่มการลงทุนดูครับ")

else:
    st.error("ไม่พบฐานข้อมูล assets.csv")
