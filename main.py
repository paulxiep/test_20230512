import pandas as pd
import streamlit as st
import datetime

st.title('Test')

order_file = st.file_uploader('Upload ข้อมูลรายการสั่งซื้อ.xlsx')
contract_file = st.file_uploader('Upload ข้อมูลสัญญาซื้อขาย.xlsx')

if order_file:
    order = pd.read_excel(order_file, dtype=str)
    order['NetAmount_THB'] = order['NetAmount_THB'].apply(float)
    order['POAmount_THB'] = order['POAmount_THB'].apply(float)

    st.subheader('Clarifications')
    st.text('Ambiguous data: look at the following subset from order table')
    temp = order[['ItemDescription', 'ReceivedQty',
                  'RemainQty', 'ReceivedAmount_THB', 'RemainAmount_THB',
                  'POAmount_THB', 'ContactNo']]
    temp = temp[temp['ContactNo'].notna()]
    st.dataframe(temp.loc[[2512, 2950, 3060, 3377]])
    st.markdown(
        '''These rows are exact same item type (based on description) from exact same contract,
        \n\nbut how much does the contract actually order? What is the correct way to aggregate these rows?
        \n\nBoth row 3060 and row 3377 have ReceivedQty and RemainQty that sum up to row 2512\'s ReceivedQty.
        \n\nWhat is the actual amount of items delivered?
        \n\nShould we assume both 3060 and 3377 are the same lot of items as 2512? 
        \n\nOr should we assume they\'re all separate lot of items?
        \n\nWhat of row 2950? Is that a continuation of 2512? Total items received are 16450, or 16450+8700?
        \n\nSince the data is this ambiguous, and request of clarification is limited in an employment test setting,
        \n\na simple assumption will be made that all rows are separate lots of items.
        \n\nThis assumption is so that something can be done, and we\'ll adhere to it for all questions answered here.''')

    q1 = order[['Company', 'NetAmount_THB']].groupby('Company').sum().sort_values('NetAmount_THB', ascending=False)

    q2 = order[['Supplier', 'POAmount_THB']].groupby('Supplier').sum().sort_values('POAmount_THB', ascending=False)

    q3 = order[['Supplier', 'Company', 'POAmount_THB']].groupby(['Supplier', 'Company']).sum().reset_index()

    q4 = order[['Company', 'PartNum', 'NetAmount_THB']].groupby(['Company', 'PartNum']).sum().reset_index()

    tabs = st.tabs(list(map(lambda x: f'Q{x}', range(1, 9))))

    with tabs[0]:
        st.subheader('Q1')
        st.text('จงหา Top 10 ของบริษัทที่มีมูลค่าซื้อสูงที่สุด')
        st.dataframe(q1)

    with tabs[1]:
        st.subheader('Q2')
        st.text('จงหา Top 10 ของผู้ขายที่มีมูลค่าการขายที่สูงที่สุด')
        st.dataframe(q2.head(10))

    with tabs[2]:
        st.subheader('Q3')
        st.text('จงหาว่าในแต่ละผู้ขาย ขายให้บริษัทใดบ้างโดยเรียงตามมูลค่าจากมากไปน้อย')
        for supplier in q2.index:
            st.text(f'Supplier: {supplier}')
            st.dataframe(
                q3[q3['Supplier'] == supplier].sort_values('POAmount_THB', ascending=False).set_index('Company').drop(
                    'Supplier', axis=1))

    with tabs[3]:
        st.subheader('Q4')
        st.text('จงหาว่าบริษัทแต่ละราย ซื้อรายการสินค้าใดมากที่สุด 10 อันดับแรก')
        for buyer in q1.index:
            st.text(f'Company (Buyer): {buyer}')
            st.dataframe(q4[q4['Company'] == buyer].sort_values('NetAmount_THB', ascending=False).head(10).set_index(
                'PartNum').drop('Company', axis=1))

    if contract_file:
        contract = pd.read_excel(contract_file, dtype=str)
        contract['ScaleQty'] = contract['ScaleQty'].apply(float)
        contract['UnitPrice'] = contract['UnitPrice'].apply(float)
        contract['Differentiate'] = contract['Differentiate'].apply(float)

        q5 = pd.merge(contract[['CPMNum', 'ExpiredDate']], order[['ContactNo', 'PartNum']], how='inner',
                      left_on='CPMNum', right_on='ContactNo').dropna(axis=0)

        contract['ContractBuyerPartNum'] = contract['CPMNum'].astype(str).apply(lambda x: x + '-') + contract['MatCode']
        order['ContractBuyerPartNum'] = order['ContactNo'].astype(str).apply(lambda x: x + '-') + order['BuyerPartNum']

        q6 = pd.merge(contract[['ContractBuyerPartNum', 'UnitPrice', 'Differentiate', 'MinOrder']],
                      order[['ContractBuyerPartNum', 'UnitPrice', 'ReceivedQty',
                             'RemainQty', 'ReceiveStatus', 'ReceivedAmount_THB', 'RemainAmount_THB', 'POAmount_THB',
                             'Company', 'Supplier']], how='outer', left_on='ContractBuyerPartNum',
                      right_on='ContractBuyerPartNum')

        q7 = q6[q6['UnitPrice_x'].notna() & q6['UnitPrice_y'].notna()]

        with tabs[4]:
            st.subheader('Q5')
            st.text('จงหารหัสรายการสินค้าที่ยังไม่หมดสัญญาซื้อขายโดยยึดจากวันที่ 31 พค 2021')
            st.text('(based on PartNum, not BuyerPartNum, null value removed)')
            st.json(
                q5[pd.to_datetime(q5['ExpiredDate']) > datetime.datetime(2021, 5, 21, 7)]['PartNum'].unique().tolist())

        with tabs[5]:
            st.subheader('Q6')
            st.text('จงเปรียบเทียบรายการสินค้าในใบสั่งซื้อว่าตรงกับในสัญญาหรือไม่')
            st.markdown('''Since there seems to be no information on contracts table on how many items are actually procured,
                        \n\nwe'll adhere all the more to the initial assumption that all indices are unrelated entries''')
            st.text('Based on the outer join between contract and orders by the Contract No:')
            st.text(f"Total indexes of the joined table is {len(q6.index)}.")
            st.text(f"Of this, {len(q6[q6['UnitPrice_x'].notna() & q6['UnitPrice_y'].notna()].index)} POs exist in the contracts table.")
            st.text(f"{len(q6[q6['UnitPrice_x'].notna() & q6['UnitPrice_y'].isna()].index)} ContractNo-BuyerPartNum has not corresponding PO in order table.")
            st.text(f"{len(q6[q6['UnitPrice_x'].isna() & q6['UnitPrice_y'].notna()].index)} POs have null contract entries.")

        with tabs[6]:
            st.subheader('Q7')
            st.text('จากข้อ 6 รายการสินค้าที่ราคาไม่ตรงกับสัญญาคิดเป็นมูลค่าเท่าใด')
            st.text(f"Out of total value of ~{int(order['POAmount_THB'].sum()//1000000)} M of POAmount of POs in order table,")
            st.text(f"~{int(q7[q7['UnitPrice_x']!=q7['UnitPrice_y']]['POAmount_THB'].sum()//1000000)} M has UnitPrices that differ between contract and actual orders")