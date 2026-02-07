import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os

# --- ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Titan Asset Manager V3.5+", page_icon="🛡️", layout="wide")

st.title("🛡️ Titan V3.5+: Wealth & Pension Simulator (Inflation Adjusted)")
st.markdown("**ห้องบัญชีและเครื่องจำลองแผนเกษียณ (เพิ่มการคำนวณค่าเงินเฟ้อ)**")

csv_file = 'assets.csv'

# --- 1. จัดการข้อมูล (Data Management - V3.5 Style) ---
if os.path.exists(csv_file):
    df = pd.read_csv(csv_file)
    
    # ตรวจสอบคอลัมน์ DCA
    if 'Monthly DCA (THB)' not in df.columns:
        df['Monthly DCA (THB)'] = 0
        df.to_csv(csv_file, index=False)

    # --- ส่วนแก้ไขข้อมูล ---
    with st.expander("📝 บันทึก/แก้ไข ทรัพย์สินและเงินออม (คลิกเพื่อเปิด)", expanded=False):
        edited_df = st.data_editor(
            df,
            num_rows="dynamic",
            column_config={
                "Category": st.column_config.SelectboxColumn(
                    "ประเภท",
                    options=["High Yield (สหกรณ์)", "Investment (กบข.)", "Stocks (หุ้นไทย)", 
                             "Mutual Fund (RMF)", "Sniper (เก็งกำไร)", "Cash (สภาพคล่อง)", "Gold (ทองคำ)"],
                    required=True
                ),
                "Value (THB)": st.column_config.NumberColumn("มูลค่าปัจจุบัน", format="%d ฿"),
                "Monthly DCA (THB)": st.column_config.NumberColumn("ออมเพิ่ม/เดือน", format="%d ฿", help="ใส่ 0 ถ้าไม่ได้เติมเงิน"),
                "Expected Return (%)": st.column_config.NumberColumn("ผลตอบแทนคาดหวัง/ปี", format="%.1f%%"),
            },
            use_container_width=True
        )

        if st.button("💾 บันทึกข้อมูล (Save)"):
            edited_df.to_csv(csv_file, index=False)
            st.success("บันทึกเรียบร้อย!")
            st.rerun()

    # --- 2. ส่วนจำลองอนาคต (Simulation Engine) ---
    st.write("---")
    st.subheader("🚀 จำลองแผนเกษียณ & ค่าเงินในอนาคต")

    # Input หลัก
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("##### ⏱️ เวลา & เป้าหมาย")
        years_to_sim = st.number_input("อีกกี่ปีเกษียณ (ทศนิยมได้)", min_value=0.1, max_value=40.0, value=9.75, step=0.25)
        target_wealth = st.number_input("เป้าหมายเงินก้อน (บาท)", min_value=1000000, value=5000000, step=500000)
    
    with col2:
        st.markdown("##### 👮‍♂️ ข้อมูลข้าราชการ")
        pension_mode = st.radio("วิธีคำนวณบำนาญ:", ["ให้ระบบคำนวณ (ละเอียด)", "ระบุเอง (Manual)"])
        
        if pension_mode == "ระบุเอง (Manual)":
            final_pension = st.number_input("ระบุยอดบำนาญ (บาท)", value=49000)
            avg_last_60_salary = 0 
        else:
            current_salary = st.number_input("เงินเดือนปัจจุบัน", value=48780)
            salary_cap = st.number_input("เงินเดือนตันที่", value=73000)
            total_gov_years_at_retire = st.number_input("อายุราชการรวมตอนเกษียณ (ปี)", value=35.10, step=0.1, format="%.2f")

    with col3:
        st.markdown("##### 📈 สมมติฐานเศรษฐกิจ")
        # Slider เงินเดือนขึ้น (ที่คุณต้องการ)
        if pension_mode != "ระบุเอง (Manual)":
            salary_growth = st.slider("เงินเดือนขึ้นเฉลี่ย (%/ปี)", 0.0, 10.0, 3.0, 0.1)
            
        safe_withdraw_rate = st.slider("ถอนเงินก้อนมาใช้ (%/ปี)", 1.0, 6.0, 4.0, 0.5)
        
        # เพิ่ม Slider เงินเฟ้อ
        inflation_rate = st.slider("อัตราเงินเฟ้อเฉลี่ย (%/ปี)", 0.0, 5.0, 3.0, 0.1)
        st.caption(f"*ใช้คำนวณมูลค่าที่แท้จริง (Real Value)")

    # --- Logic การคำนวณ ---
    if not edited_df.empty:
        
        # [A] คำนวณบำนาญ (Pension Projection)
        if pension_mode == "ให้ระบบคำนวณ (ละเอียด)":
            sim_salary = current_salary
            salary_history = []
            sim_years = int(years_to_sim) + 1 
            
            for y in range(1, sim_years + 1):
                # คำนวณการขึ้นเงินเดือน
                sim_salary = sim_salary * (1 + salary_growth / 100)
                # เช็คเพดานตัน
                if sim_salary > salary_cap: 
                    sim_salary = salary_cap
                
                # เก็บข้อมูล 5 ปีสุดท้าย
                if y > (sim_years - 5):
                    salary_history.extend([sim_salary] * 12)

            # เติมข้อมูลให้ครบ 60 เดือน (กรณีเกษียณเร็ว)
            while len(salary_history) < 60:
                salary_history.insert(0, current_salary)
                
            last_60_months = salary_history[-60:]
            avg_last_60_salary = sum(last_60_months) / 60
            
            # สูตรบำนาญ
            raw_pension = (avg_last_60_salary * total_gov_years_at_retire) / 50
            max_pension = avg_last_60_salary * 0.70
            final_pension = min(raw_pension, max_pension)

        # [B] คำนวณเงินก้อน (Wealth Simulation)
        current_assets_val = edited_df['Value (THB)'].sum()
        wealth_over_time = {0: current_assets_val}
        
        sim_df = edited_df.copy()
        sim_df['Monthly Rate'] = sim_df['Expected Return (%)'] / 100 / 12
        
        months_total = int(years_to_sim * 12)
        months = np.arange(1, months_total + 1)
        
        asset_growth_history = []
        is_coop = sim_df['Category'] == "High Yield (สหกรณ์)"

        for m in months:
            # 1. สินทรัพย์ทั่วไป (ทบต้น)
            sim_df.loc[~is_coop, 'Value (THB)'] = (sim_df.loc[~is_coop, 'Value (THB)'] * (1 + sim_df.loc[~is_coop, 'Monthly Rate'])) + sim_df.loc[~is_coop, 'Monthly DCA (THB)']
            # 2. สหกรณ์ (ไม่ทบต้น)
            sim_df.loc[is_coop, 'Value (THB)'] = sim_df.loc[is_coop, 'Value (THB)'] + sim_df.loc[is_coop, 'Monthly DCA (THB)']

            wealth_over_time[m] = sim_df['Value (THB)'].sum()
            
            if m % 12 == 0 or m == months_total:
                 for index, row in sim_df.iterrows():
                    asset_growth_history.append({
                        "Month": m, "Year": m / 12,
                        "Category": row['Category'], "Asset Name": row['Asset Name'], "Value": row['Value (THB)']
                    })

        final_wealth_nominal = wealth_over_time[months_total] if months_total > 0 else current_assets_val
        
        # [C] คำนวณค่าเงินเฟ้อ (Real Value Calculation)
        inflation_factor = (1 + inflation_rate/100) ** years_to_sim
        
        final_wealth_real = final_wealth_nominal / inflation_factor
        final_pension_real = final_pension / inflation_factor
        
        # [D] คำนวณรายได้ต่อเดือน
        coop_income_monthly = (sim_df[is_coop]['Value (THB)'] * (sim_df[is_coop]['Expected Return (%)'] / 100)).sum() / 12
        other_wealth = sim_df[~is_coop]['Value (THB)'].sum()
        other_income_monthly = (other_wealth * (safe_withdraw_rate/100)) / 12
        
        total_monthly_nominal = final_pension + coop_income_monthly + other_income_monthly
        total_monthly_real = total_monthly_nominal / inflation_factor

        # --- Display Result ---
        st.info(f"📊 **สรุปสถานะ ณ วันเกษียณ (อีก {years_to_sim} ปี)** | เงินเฟ้อคาดการณ์: {inflation_rate}%")
        
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("💰 เงินก้อน (ตัวเลข)", f"{final_wealth_nominal/1000000:,.2f} ล้าน฿", "ยอดในบัญชีวันนั้น")
        k2.metric("🥪 มูลค่าจริง (หักเฟ้อ)", f"{final_wealth_real/1000000:,.2f} ล้าน฿", 
                  f"อำนาจซื้อเท่ากับเงินวันนี้ (หายไป {((final_wealth_nominal-final_wealth_real)/1000000):.1f}M)", delta_color="inverse")
        
        k3.metric("🏛️ บำนาญ (ตัวเลข)", f"{final_pension:,.0f} ฿", f"ฐานเงินเดือนเฉลี่ย: {avg_last_60_salary:,.0f}")
        k4.metric("🥪 บำนาญ (มูลค่าจริง)", f"{final_pension_real:,.0f} ฿", "เทียบเท่าเงินวันนี้")

        st.write("---")
        
        # แสดงรายได้สุทธิ เปรียบเทียบ
        col_inc1, col_inc2 = st.columns(2)
        with col_inc1:
            st.success(f"💵 **รายได้รวม (ตัวเลข): {total_monthly_nominal:,.0f} บาท/เดือน**")
            st.progress(min(total_monthly_nominal/100000, 1.0))
        with col_inc2:
            st.warning(f"🧺 **รายได้รวม (หักเฟ้อ): {total_monthly_real:,.0f} บาท/เดือน**")
            st.progress(min(total_monthly_real/100000, 1.0))
            st.caption(f"*นี่คือความรู้สึกรวยจริงๆ ที่ท่านจะได้รับ (เมื่อเทียบกับค่าครองชีพวันนี้)*")

        # --- Graphs ---
        st.write("---")
        col_pie, col_bar = st.columns(2)
        
        with col_pie:
            st.subheader("🥧 สัดส่วนเงินก้อน (Nominal)")
            fig_pie = px.pie(sim_df, values='Value (THB)', names='Category', 
                             title=f'รวม {final_wealth_nominal/1000000:,.2f} ล้านบาท', hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with col_bar:
            st.subheader("💵 แหล่งที่มารายได้ (Nominal)")
            income_df = pd.DataFrame([
                {"Source": "บำนาญ", "Amount": final_pension},
                {"Source": "ปันผลสหกรณ์", "Amount": coop_income_monthly},
                {"Source": "ถอนเงินลงทุน", "Amount": other_income_monthly}
            ])
            fig_bar = px.bar(income_df, x="Source", y="Amount", color="Source", 
                             text_auto=',.0f', title=f"รวม {total_monthly_nominal:,.0f} บาท/เดือน")
            fig_bar.update_layout(showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)

        st.subheader("📈 เส้นทางความมั่งคั่ง (Wealth Projection)")
        
        # สร้างเส้น Real Value มาเทียบ
        real_wealth_line = [v / ((1 + inflation_rate/100) ** (m/12)) for m, v in wealth_over_time.items()]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=list(wealth_over_time.keys()), y=list(wealth_over_time.values()), 
                                 mode='lines', name='ตัวเลขเงิน (Nominal)', line=dict(color='#00CC96', width=3)))
        fig.add_trace(go.Scatter(x=list(wealth_over_time.keys()), y=real_values if 'real_values' in locals() else real_wealth_line, 
                                 mode='lines', name='มูลค่าจริง (Real)', line=dict(color='#FFA15A', width=2, dash='dot')))
        
        fig.update_layout(height=400, xaxis_title="เดือน", yaxis_title="บาท", title="เปรียบเทียบ: เงินที่เห็น vs เงินที่ใช้ได้จริง")
        st.plotly_chart(fig, use_container_width=True)
        
        if asset_growth_history:
            st.subheader("🧩 การเติบโตแยกตามสินทรัพย์")
            area_df = pd.DataFrame(asset_growth_history)
            fig_area = px.area(area_df, x="Year", y="Value", color="Category", groupnorm=None)
            st.plotly_chart(fig_area, use_container_width=True)

    else:
        st.warning("⚠️ กรุณากรอกข้อมูลสินทรัพย์ด้านบนก่อนครับ")
else:
    st.error("ไม่พบฐานข้อมูล assets.csv")
