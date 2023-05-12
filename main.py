import streamlit as st
import pandas as pd
import numpy as np

st.title('Test')

order_file = st.file_uploader('Upload ข้อมูลรายการสั่งซื้อ.xlsx')

if order_file:
    order = pd.read_excel(order_file, dtype=str)
    order['NetAmount_THB'] = order['NetAmount_THB'].apply(float)
    order['POAmount_THB'] = order['POAmount_THB'].apply(float)

    q1 = order[['Company', 'NetAmount_THB']].groupby('Company').sum().sort_values('NetAmount_THB', ascending=False)

    q2 = order[['Supplier', 'POAmount_THB']].groupby('Supplier').sum().sort_values('POAmount_THB', ascending=False)

    q3 = order[['Supplier', 'Company', 'POAmount_THB']].groupby(['Supplier', 'Company']).sum().reset_index()

    q4 = order[['Company', 'BuyerPartNum', 'NetAmount_THB']].groupby(['Company', 'BuyerPartNum']).sum().reset_index()

    c1, c2 = st.columns(2)

    with c1:
        st.subheader('Q1')
        st.text('จงหา Top 10 ของบริษัทที่มีมูลค่าซื้อสูงที่สุด')
        st.dataframe(q1)

    with c2:
        st.subheader('Q2')
        st.text('จงหา Top 10 ของผู้ขายที่มีมูลค่าการขายที่สูงที่สุด')
        st.dataframe(q2.head(10))

    c3, c4 = st.columns(2)

    with c3:
        st.subheader('Q3')
        st.text('จงหาว่าในแต่ละผู้ขาย ขายให้บริษัทใดบ้างโดยเรียงตามมูลค่าจากมากไปน้อย')
        for supplier in q2.index:
            st.text(f'Supplier: {supplier}')
            st.dataframe(
                q3[q3['Supplier'] == supplier].sort_values('POAmount_THB', ascending=False).set_index('Company').drop(
                    'Supplier', axis=1))

    with c4:
        st.subheader('Q4')
        st.text('4.	จงหาว่าบริษัทแต่ละราย ซื้อรายการสินค้าใดมากที่สุด 10 อันดับแรก')
        for buyer in q1.index:
            st.text(f'Company (Buyer): {buyer}')
            st.dataframe(q4[q4['Company']==buyer].sort_values('NetAmount_THB', ascending=False).head(10).set_index('BuyerPartNum').drop('Company', axis=1))
