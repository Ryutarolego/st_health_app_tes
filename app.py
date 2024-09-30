"""
# 目的
Streamlitで、各人の健康データ登録・管理アプリを作りたい。
 
# ユースケース
## データ登録時
- 「データ登録」のタブを選択する
- 健康データが記録されたCSVファイルをWebアプリにアップロードする
- 年齢、名前、性別を入力する
- 「登録」ボタンを押す
- 画面に「登録しました」メッセージが表示され、入力欄が空になる
- 別のファイルをアップロードすると、再度入力欄が表示される

## データ閲覧時
- 「データ閲覧」のタブを選択する
- 画面に日付、時刻、年齢、名前、性別をカラムに持つテーブルが表示されるので、任意の行を選択する
- 「閲覧」ボタンを押すと、健康データのCSVをロードしてテーブル形式で画面に表示する

# 保存する情報
次のデータは、マスターCSVに保存される。
- 日付: datetime データアップロード時刻から自動入力
- 時刻: datetime データアップロード時刻から自動入力
- 名前: str ユーザ入力項目
- 年齢: int ユーザ入力項目
- 性別: Literal['Man', 'Woman'] ユーザ
        selected_file = selected_rows["CSVファイル名"].iloc[0]入力項目
- CSVファイルのファイル名: UUID 自動生成
健康データのCSVファイルは、「data」フォルダ以下に保存され、UUIDをファイル名として持つ。
"""
import os
import uuid
from datetime import datetime
import sqlite3

import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# データフォルダの設定
root = os.path.dirname(__file__)
data_folder = os.path.join(root, 'data')
# master_csv = os.path.join(root, 'master_data.csv')
# SQLiteデータベースのファイル名を指定
db_name = os.path.join(root, 'master_data.db')

# 保存先フォルダが存在しない場合は作成
if not os.path.exists(data_folder):
    os.makedirs(data_folder)

# # マスターCSVが存在しない場合は新規作成
# if not os.path.exists(master_csv):
#     df = pd.DataFrame(columns=['日付', '時刻', '名前', '年齢', '性別', 'CSVファイル名'])
#     df.to_csv(master_csv, index=False)


# SQLiteデータベースに接続
def get_db_connection():
    conn = sqlite3.connect(db_name)
    return conn

# テーブルがない場合は作成
def create_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS master_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            日付 TEXT,
            時刻 TEXT,
            名前 TEXT,
            年齢 INTEGER,
            性別 TEXT,
            CSVファイル名 TEXT
        )
    ''')
    conn.commit()
    conn.close()

# データベースからマスターCSVを読み込み
def load_master_data():
    conn = get_db_connection()
    query = "SELECT * FROM master_data"
    # query = "SELECT 日付, 時刻, 名前, 年齢, 性別, CSVファイル名 FROM master_data"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# データベースに新規エントリを挿入
def insert_new_entry(date_str, time_str, name, age, gender, file_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO master_data (日付, 時刻, 名前, 年齢, 性別, CSVファイル名)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (date_str, time_str, name, age, gender, file_id))
    conn.commit()
    conn.close()

# データベースのエントリを更新
def update_entry(entry_id, name, age, gender):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE master_data
        SET 名前 = ?, 年齢 = ?, 性別 = ?
        WHERE id = ?
    ''', (name, age, gender, entry_id))
    conn.commit()
    conn.close()

# データベースのエントリを削除
def delete_entry(entry_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f'DELETE FROM master_data WHERE id = {entry_id}')
    conn.commit()
    conn.close()

# データ登録の処理
def data_registration():
    st.title("データ登録")
    
    # セッションステートの初期化（必要なら）
    if 'registration_submitted' not in st.session_state:
        st.session_state.registration_submitted = False
    
    # 登録が完了していない場合のみ入力欄を表示
    if not st.session_state.registration_submitted:
        # CSVファイルのアップロード
        uploaded_file = st.file_uploader("健康データをCSVファイルでアップロードしてください", type=["csv"])
        
        if uploaded_file is not None:
            name = st.text_input("名前")
            age = st.number_input("年齢", min_value=0, max_value=120, step=1)
            gender = st.selectbox("性別", options=["Man", "Woman"])
            
            if st.button("登録"):
                # 日付と時刻の取得
                now = datetime.now()
                date_str = now.strftime("%Y-%m-%d")
                time_str = now.strftime("%H:%M:%S")
                
                # UUIDでファイル名を生成し保存
                file_id = str(uuid.uuid4())
                file_path = os.path.join(data_folder, f"{file_id}.csv")
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # 新規エントリをSQLiteに挿入
                insert_new_entry(date_str, time_str, name, age, gender, file_id)

                # # マスターCSVにデータを登録
                # new_entry = pd.DataFrame({
                #     "日付": [date_str],
                #     "時刻": [time_str],
                #     "名前": [name],
                #     "年齢": [age],
                #     "性別": [gender],
                #     "CSVファイル名": [file_id]
                # })
                # master_data = pd.read_csv(master_csv)
                # master_data = pd.concat([master_data, new_entry], ignore_index=True)
                # master_data.to_csv(master_csv, index=False)
                
                
                # セッションステートを更新して入力欄を非表示にする
                st.session_state.registration_submitted = True
                st.rerun()
    
    else:
        st.success("登録しました")
        # st.write("データは既に登録されています。")
        if st.button("新しいデータを登録する"):
            # セッションステートをリセット
            st.session_state.registration_submitted = False

# データ閲覧の処理
def data_viewing():
    st.title("データ閲覧・編集")
    
    # マスターCSVを読み込む
    # master_data = pd.read_csv(master_csv)
    master_data = load_master_data()
    if master_data.empty:
        st.warning("登録されたデータがありません。")
        return
        master_data = load_master_data()

    # AgGridの設定
    gb = GridOptionsBuilder.from_dataframe(master_data)
    gb.configure_selection(selection_mode="single")  # 単一行選択
    gb.configure_columns(["名前", "年齢", "性別"], editable=True)  # 編集可能にする列を指定
    gb.configure_column("CSVファイル名", header_name="", hide=True)  # CSVファイル名列は非表示
    grid_options = gb.build()
    
    # AgGridでデータフレーム表示 (editable=Trueで編集可能に設定)
    grid_response = AgGrid(
        master_data,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        data_return_mode='AS_INPUT',
        enable_enterprise_modules=False,
        height=300,
        width='100%',
        reload_data=False,
    )
    
    # 編集されたデータを取得
    updated_data: pd.DataFrame = grid_response['data']
    selected_rows: pd.DataFrame = grid_response['selected_rows']
    
    # 保存ボタンを追加して、編集内容を保存する
    if st.button("編集内容を保存"):
        # 更新されたデータをマスターCSVに上書き保存
        # updated_df = pd.DataFrame(updated_data)
        # updated_df.to_csv(master_csv, index=False)
        for _, updated_row in updated_data.iterrows():
            entry_id = updated_row['id']
            update_entry(entry_id, updated_row['名前'], updated_row['年齢'], updated_row['性別'])
        st.success("編集内容が保存されました")
    
    # 選択された行に基づいて、詳細データを表示
    if selected_rows is not None and len(selected_rows) > 0:
        selected_row = selected_rows.iloc[0]
        selected_id = selected_row['id']
        
        selected_file = selected_row["CSVファイル名"]
        file_path = os.path.join(data_folder, f"{selected_file}.csv")
        if st.button("選択した行を削除"):
            # 選択された行を削除
            delete_entry(selected_id)
            # updated_df = pd.DataFrame(updated_data)
            # updated_df = updated_df[updated_df["CSVファイル名"] != selected_file]  # 選択したファイル名の行を除外
            # updated_df.to_csv(master_csv, index=False)
            st.success("選択したデータが削除されました")
            st.rerun()  # 削除後に画面を更新

        if st.button("閲覧"):
            if os.path.exists(file_path):
                # CSVファイルを表示
                data = pd.read_csv(file_path)
                # st.write(f"健康データ: {selected_rows[0]['名前']} の詳細")
                st.dataframe(data)
            else:
                st.error("ファイルが見つかりません。")



def main():
    st.sidebar.title("健康データ管理アプリ")
    # app_mode = st.sidebar.selectbox("選択してください", ["データ登録", "データ閲覧"])
    app_mode = st.sidebar.selectbox("選択してください", ["データ閲覧", "データ登録"])

    if app_mode == "データ登録":
        data_registration()
    elif app_mode == "データ閲覧":
        data_viewing()

if __name__ == "__main__":
    create_table()  # 初回起動時にテーブルを作成
    main()
