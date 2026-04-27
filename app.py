import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime, timedelta
from reportlab.platypus import SimpleDocTemplate, Table
from PIL import Image, ImageDraw

# ---------------- DATABASE ---------------- #
from sqlalchemy import create_engine
# from sqlalchemy.pool import NullPool
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Fetch variables
USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")
# Construct the SQLAlchemy connection string
DATABASE_URL =f"postgresql+psycopg2://postgres.xwsxtywrebwgtwgebuyp:lAP4U4KlmoE5rLvw@aws-1-ap-south-1.pooler.supabase.com:6543/postgres?sslmode=require"
engine = create_engine(DATABASE_URL)
# ---------------- UI ---------------- #
st.title("Hitesh Agro Foods")
st.subheader("📦 Inventory Management System")

menu = st.sidebar.selectbox("Menu", ["Inventory", "Raw Material", "Sell", "Reports", "Convert","Loose Packets"])

packaging_options = [
    "10gm", "20gm", "50gm", "100gm",
    "250gm", "500gm", "1kg", "5kg", "10kg","30kg","50kg"
]

# ======================================================
# 📦 INVENTORY
# ======================================================
if menu == "Inventory":
    st.subheader("Add Inventory")

    item = st.text_input("Item")
    size = st.selectbox("Packaging Size",packaging_options)
    packets = st.number_input("Qty in Packets", min_value=0)
    kgs = st.number_input("Qty in KGs", min_value=0.0)

    # ---------------- ADD ITEM ---------------- #
    if st.button("Add Item"):

        item_clean = item.strip().lower()
        size_clean = size.strip().lower().replace(" ", "")

        data = pd.read_sql("SELECT * FROM inventory", engine)

        match_found = False

        for _, row in data.iterrows():
            db_item = str(row["item"]).strip().lower()
            db_size = str(row["packaging_size"]).strip().lower().replace(" ", "")

            if db_item == item_clean and db_size == size_clean:
                new_packets = int(row["qty_packets"]) + int(packets)
                new_kgs = float(row["qty_kgs"]) + float(kgs)

                with engine.begin() as conn:
                    conn.exec_driver_sql(
                        "UPDATE inventory SET qty_packets=%s, qty_kgs=%s WHERE id=%s",
                        (new_packets, new_kgs, int(row["id"]))
                    )

                st.success("Updated existing inventory ✅")
                match_found = True
                break

        if not match_found:
            df = pd.DataFrame(
                [[item, size, int(packets), float(kgs), datetime.now()]],
                columns=["item","packaging_size","qty_packets","qty_kgs","date"]
            )

            df.to_sql("inventory", engine, if_exists="append", index=False)

            st.success("Added new item ✅")

        st.rerun()

    # ---------------- SHOW TABLE ---------------- #
    data = pd.read_sql("SELECT * FROM inventory", engine)
    st.dataframe(data)

    # ---------------- DELETE SECTION ---------------- #
    st.divider()
    st.subheader("🗑 Delete Item (by ID)")

    if len(data) > 0:
        id_to_delete = st.number_input("Enter ID", min_value=1, step=1)

        confirm = st.checkbox("Confirm deletion")

        if st.button("Delete"):
            if confirm:
                with engine.begin() as conn:
                    conn.exec_driver_sql(
                        "DELETE FROM inventory WHERE id = %s",
                        (int(id_to_delete),)
                    )

                st.success(f"Deleted ID {id_to_delete}")
                st.rerun()
            else:
                st.warning("Please confirm")
    else:
        st.info("No data available")
# ======================================================
# 🧪 RAW MATERIAL
# ======================================================
elif menu == "Raw Material":
    st.subheader("🧪 Raw Material")

    # ---------------- ADD RAW MATERIAL ---------------- #
    st.markdown("### ➕ Add Raw Material")

    item = st.text_input("Raw Item")
    size = st.text_input("Size")
    qty = st.number_input("Quantity", min_value=0.0)

    if st.button("Add Raw Material", key="add_raw"):

     item_clean = item.strip().lower()
     size_clean = size.strip().lower()

    df_existing = pd.read_sql("SELECT * FROM raw_material", engine)

    found = False

    for _, r in df_existing.iterrows():
        db_item = str(r["item"]).strip().lower()
        db_size = str(r["size"]).strip().lower()

        if db_item == item_clean and db_size == size_clean:
            # ✅ UPDATE EXISTING ROW
            new_qty = float(r["qty"]) + float(qty)

            with engine.begin() as conn:
                conn.exec_driver_sql(
                    "UPDATE raw_material SET qty=%s WHERE id=%s",
                    (new_qty, int(r["id"]))
                )

            found = True
            break

    if not found:
        # ✅ INSERT NEW ROW
        df_add = pd.DataFrame(
            [[item_clean, size_clean, float(qty), datetime.now()]],
            columns=["item", "size", "qty", "date"]
        )
        df_add.to_sql("raw_material", engine, if_exists="append", index=False)

    st.success("Added Successfully ✅")
    st.rerun()

    # ---------------- SHOW DATA ---------------- #
    st.divider()
    st.subheader("📊 Raw Material Data")

    df = pd.read_sql("SELECT * FROM raw_material", engine)
    st.dataframe(df)

    # ======================================================
    # 🛒 USE RAW MATERIAL
    # ======================================================
    st.divider()
    st.subheader("🛒 Use Raw Material")

    if len(df) == 0:
        st.warning("No raw material available")
    else:
        item_use = st.selectbox("Select Raw Item", df["item"].unique())

        item_data = df[df["item"] == item_use]

        size_use = st.selectbox("Select Size", item_data["size"].unique())

        row = item_data[item_data["size"] == size_use].iloc[0]

        try:
            available_qty = float(row["qty"])
        except:
            available_qty = 0.0

        st.write(f"Available Quantity: {available_qty}")

        use_qty = st.number_input("Quantity to Use", min_value=0.1)

        if st.button("Use Raw Material"):
            if available_qty >= use_qty:

                new_qty = available_qty - use_qty

                with engine.begin() as conn:
                    conn.exec_driver_sql(
                        "UPDATE raw_material SET qty=%s WHERE id=%s",
                        (new_qty, int(row["id"]))
                    )

                st.success(f"Used {use_qty} of {item_use} ✅")
                st.rerun()
            else:
                st.error("Not enough material ❌")

    # ======================================================
    # 🗑 DELETE RAW MATERIAL
    # ======================================================
    st.divider()
    st.subheader("🗑 Delete Raw Material")

    if len(df) > 0:
        delete_id = st.number_input("Enter ID to delete", min_value=1, step=1)

        confirm_delete = st.checkbox("Confirm deletion")

        if st.button("Delete Raw Material"):
            if confirm_delete:
                with engine.begin() as conn:
                    conn.exec_driver_sql(
                        "DELETE FROM raw_material WHERE id=%s",
                        (int(delete_id),)
                    )

                st.success(f"Deleted ID {delete_id} ✅")
                st.rerun()
            else:
                st.warning("Please confirm deletion ⚠️")
    else:
        st.info("No raw material data available")
    
# ======================================================
# 🛒 SELL
# ======================================================
elif menu == "Sell":
    st.subheader("🛒 Sell Product")

    # ================= BUYER DETAILS ================= #
    st.markdown("### 👤 Buyer Details")
    buyer_name = st.text_input("Buyer Name")
    buyer_address = st.text_area("Buyer Address")

    # ================= LOAD DATA ================= #
    data = pd.read_sql("SELECT * FROM inventory", engine)

    if len(data) == 0:
        st.warning("No inventory available")
    else:
        # ---------------- SELECT ITEM ---------------- #
        item = st.selectbox("Select Item", data["item"].unique())

        item_data = data[data["item"] == item]

        # ---------------- SELECT PACKAGING ---------------- #
        packaging = st.selectbox(
            "Select Packaging Size",
            item_data["packaging_size"].unique()
        )

        row = item_data[item_data["packaging_size"] == packaging].iloc[0]

        # ---------------- SAFE VALUES ---------------- #
        try:
            packets = int(float(row["qty_packets"]))
        except:
            packets = 0

        try:
            kgs = float(row["qty_kgs"])
        except:
            kgs = 0.0

        # ---------------- SHOW STOCK ---------------- #
        st.markdown("### 📦 Current Stock")
        col1, col2 = st.columns(2)
        col1.metric("Packets (Bags)", packets)
        col2.metric("Loose KGs", kgs)

        # ======================================================
        # 📦 CONVERT KG → PACKETS (STANDARD 30KG)
        # ======================================================
        st.divider()
        st.subheader("📦 Convert KG → Packets")

        STANDARD_PACKET_KG = 30

        convert_kgs = st.number_input("Enter KG to convert", min_value=0.1)

        if st.button("Convert"):
            if kgs >= convert_kgs:

                packets_created = int(convert_kgs // STANDARD_PACKET_KG)

                if packets_created == 0:
                    st.error("❌ Minimum 30kg required for 1 packet")
                else:
                    kg_used = packets_created * STANDARD_PACKET_KG

                    new_packets = packets + packets_created
                    new_kgs = kgs - kg_used

                    with engine.begin() as conn:
                        conn.exec_driver_sql(
                            "UPDATE inventory SET qty_packets=%s, qty_kgs=%s WHERE id=%s",
                            (new_packets, new_kgs, int(row["id"]))
                        )

                    st.success(f"✅ Created {packets_created} packets (30kg each)")
                    st.rerun()

            else:
                st.error("Not enough KG")

        # ======================================================
        # 🛒 SELL SECTION
        # ======================================================
        st.divider()
        st.subheader("🛒 Sell")

        sale_type = st.radio("Sell By", ["Packets", "Kgs"])

        # ---------------- SELL PACKETS ---------------- #
        if sale_type == "Packets":
            qty_packets = int(st.number_input("Packets to Sell", min_value=1))

            if st.button("Sell Packets"):

                if buyer_name.strip() == "" or buyer_address.strip() == "":
                    st.error("Enter buyer details ❌")

                elif packets < qty_packets:
                    st.error(f"Only {packets} packets available ❌")

                else:
                    new_packets = packets - qty_packets

                    with engine.begin() as conn:
                        # UPDATE INVENTORY
                        conn.exec_driver_sql(
                            "UPDATE inventory SET qty_packets=%s WHERE id=%s",
                            (new_packets, int(row["id"]))
                        )

                        # INSERT INTO SALES
                        conn.exec_driver_sql(
                            """INSERT INTO sales 
                            (item, packaging_size, quantity, sale_type, buyer_name, buyer_address, date)
                            VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                            (item, packaging, qty_packets, "Packets", buyer_name, buyer_address, datetime.now())
                        )

                    st.success(f"✅ Sold {qty_packets} packets to {buyer_name}")
                    st.rerun()

        # ---------------- SELL KGS ---------------- #
        else:
            qty_kgs = float(st.number_input("KGs to Sell", min_value=0.1))

            if st.button("Sell KGs"):

                if buyer_name.strip() == "" or buyer_address.strip() == "":
                    st.error("Enter buyer details ❌")

                elif kgs < qty_kgs:
                    st.error(f"Only {kgs} KGs available ❌")

                else:
                    new_kgs = kgs - qty_kgs

                    with engine.begin() as conn:
                        # UPDATE INVENTORY
                        conn.exec_driver_sql(
                            "UPDATE inventory SET qty_kgs=%s WHERE id=%s",
                            (new_kgs, int(row["id"]))
                        )

                        # INSERT INTO SALES
                        conn.exec_driver_sql(
                            """INSERT INTO sales 
                            (item, packaging_size, quantity, sale_type, buyer_name, buyer_address, date)
                            VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                            (item, packaging, qty_kgs, "Kgs", buyer_name, buyer_address, datetime.now())
                        )

                    st.success(f"✅ Sold {qty_kgs} KGs to {buyer_name}")
                    st.rerun()
# ======================================================
# 📊 REPORTS
# ======================================================
elif menu == "Reports":
    st.subheader("📊 Reports")

    report_type = st.selectbox(
        "Select Report",
        ["Inventory", "Sales", "Loose Packets"]
    )

    # ======================================================
    # 📦 INVENTORY REPORT (WITH RAW MATERIAL)
    # ======================================================
    if report_type == "Inventory":

        inv_df = pd.read_sql("SELECT * FROM inventory", engine)
        raw_df = pd.read_sql("SELECT * FROM raw_material", engine)

        st.subheader("📦 Inventory")
        st.dataframe(inv_df)

        st.subheader("🧪 Raw Material")
        st.dataframe(raw_df)

        st.divider()

        # ---------------- DOWNLOAD ---------------- #

        # Excel
        if st.button("Download Excel", key="inv_excel"):
            file = "inventory_report.xlsx"
            with pd.ExcelWriter(file) as writer:
                inv_df.to_excel(writer, sheet_name="Inventory", index=False)
                raw_df.to_excel(writer, sheet_name="Raw Material", index=False)

            with open(file, "rb") as f:
                st.download_button("Download Excel File", f, file_name=file, key="inv_excel_dl")

        # PDF
        if st.button("Download PDF", key="inv_pdf"):
            file = "inventory_report.pdf"

            doc = SimpleDocTemplate(file)
            elements = []

            elements.append(Table([["INVENTORY"]]))
            elements.append(Table([inv_df.columns.tolist()] + inv_df.values.tolist()))

            elements.append(Table([["RAW MATERIAL"]]))
            elements.append(Table([raw_df.columns.tolist()] + raw_df.values.tolist()))

            doc.build(elements)

            with open(file, "rb") as f:
                st.download_button("Download PDF File", f, file_name=file, key="inv_pdf_dl")

        # JPG
        if st.button("Download JPG", key="inv_jpg"):
            file = "inventory_report.jpg"

            img = Image.new("RGB", (1000, 600), "white")
            draw = ImageDraw.Draw(img)

            text = "INVENTORY:\n" + str(inv_df.head()) + "\n\nRAW MATERIAL:\n" + str(raw_df.head())

            draw.text((10, 10), text, fill="black")

            img.save(file)

            with open(file, "rb") as f:
                st.download_button("Download JPG File", f, file_name=file, key="inv_jpg_dl")

    # ======================================================
    # 🛒 SALES REPORT
    # ======================================================
    elif report_type == "Sales":

        period = st.selectbox("Period", ["Today", "Weekly", "Monthly"])

        try:
            df = pd.read_sql("SELECT * FROM sales", engine)
            df["date"] = pd.to_datetime(df["date"])

            if period == "Today":
                df = df[df["date"].dt.date == datetime.today().date()]
            elif period == "Weekly":
                df = df[df["date"] >= datetime.now() - timedelta(days=7)]
            else:
                df = df[df["date"] >= datetime.now() - timedelta(days=30)]

        except:
            st.warning("No sales data available")
            df = pd.DataFrame()

        st.dataframe(df)

        # ---------------- DOWNLOAD ---------------- #

        # Excel
        if st.button("Download Excel", key="sales_excel"):
            file = "sales.xlsx"
            df.to_excel(file, index=False)
            with open(file, "rb") as f:
                st.download_button("Download Excel File", f, file_name=file, key="sales_excel_dl")

        # PDF
        if st.button("Download PDF", key="sales_pdf"):
            file = "sales.pdf"

            doc = SimpleDocTemplate(file)
            table = Table([df.columns.tolist()] + df.values.tolist())
            doc.build([table])

            with open(file, "rb") as f:
                st.download_button("Download PDF File", f, file_name=file, key="sales_pdf_dl")

        # JPG
        if st.button("Download JPG", key="sales_jpg"):
            file = "sales.jpg"

            img = Image.new("RGB", (900, 500), "white")
            draw = ImageDraw.Draw(img)
            draw.text((10, 10), str(df.head()), fill="black")
            img.save(file)

            with open(file, "rb") as f:
                st.download_button("Download JPG File", f, file_name=file, key="sales_jpg_dl")

    # ======================================================
    # 📦 LOOSE PACKETS REPORT
    # ======================================================
    else:

        df = pd.read_sql("SELECT * FROM loose_packets", engine)
        st.dataframe(df)

        # ---------------- DOWNLOAD ---------------- #

        # Excel
        if st.button("Download Excel", key="loose_excel"):
            file = "loose_packets.xlsx"
            df.to_excel(file, index=False)
            with open(file, "rb") as f:
                st.download_button("Download Excel File", f, file_name=file, key="loose_excel_dl")

        # PDF
        if st.button("Download PDF", key="loose_pdf"):
            file = "loose_packets.pdf"

            doc = SimpleDocTemplate(file)
            table = Table([df.columns.tolist()] + df.values.tolist())
            doc.build([table])

            with open(file, "rb") as f:
                st.download_button("Download PDF File", f, file_name=file, key="loose_pdf_dl")

        # JPG
        if st.button("Download JPG", key="loose_jpg"):
            file = "loose_packets.jpg"

            img = Image.new("RGB", (900, 500), "white")
            draw = ImageDraw.Draw(img)
            draw.text((10, 10), str(df.head()), fill="black")
            img.save(file)

            with open(file, "rb") as f:
                st.download_button("Download JPG File", f, file_name=file, key="loose_jpg_dl")
elif menu == "Convert":
    st.subheader("📦 Convert KG → Packet (Flexible)")

    data = pd.read_sql("SELECT * FROM inventory", engine)

    if len(data) == 0:
        st.warning("No inventory")
    else:
        item = st.selectbox("Item", data["item"].unique())

        item_data = data[data["item"] == item]

        size = st.selectbox("Packaging Size", item_data["packaging_size"].unique())

        row = item_data[item_data["packaging_size"] == size].iloc[0]

        packets = int(row["qty_packets"])
        kgs = float(row["qty_kgs"])

        st.write(f"Packets: {packets}")
        st.write(f"Loose KGs: {kgs}")
        convert_kgs = st.number_input("Enter KG to convert into ONE packet", min_value=0.1)

        if st.button("Convert"):
            if kgs >= convert_kgs:

                new_packets = packets + 1
                new_kgs = kgs - convert_kgs

                with engine.begin() as conn:
                    conn.exec_driver_sql(
                        "UPDATE inventory SET qty_packets=%s, qty_kgs=%s WHERE id=%s",
                        (new_packets, new_kgs, int(row["id"]))
                    )

                st.success(f"Created 1 packet of {convert_kgs} KG")
                st.rerun()
            else:
                st.error("Not enough KG")
elif menu == "Loose Packets":
    st.subheader("📦 Add Loose Packets")

    # ADD SECTION
    item = st.text_input("Item")
    packaging = st.selectbox("Packaging Size", packaging_options)
    qty = st.number_input("Packets", min_value=1)

    if st.button("Add Loose Packets"):
        with engine.begin() as conn:
            conn.exec_driver_sql(
                 "INSERT INTO loose_packets (item, packaging_size, qty_packets, date) VALUES (%s,%s,%s,%s)",
                 (item, packaging, qty, datetime.now())
        )
    st.success("Added successfully")

    st.divider()
    st.subheader("📊 Loose Packets Data")
    df = pd.read_sql("SELECT * FROM loose_packets", engine)
    st.dataframe(df)

    # ================= INSIDE SAME BLOCK =================
    st.divider()
    st.subheader("🛒 Use / Sell Loose Packets")

    if len(df) > 0:
        item = st.selectbox("Select Item (Loose)", df["item"].unique())
        item_data = df[df["item"] == item]

        packaging = st.selectbox(
            "Select Packaging Size (Loose)",
            item_data["packaging_size"].unique()
        )

        row = item_data[item_data["packaging_size"] == packaging].iloc[0]

        packets = int(row["qty_packets"])

        qty_sell = st.number_input("Packets to Use", min_value=1)

        if st.button("Use Loose Packets"):
            if packets >= qty_sell:
                new_packets = packets - qty_sell

                with engine.begin() as conn:
                    conn.exec_driver_sql(
                        "UPDATE loose_packets SET qty_packets=%s WHERE id=%s",
                        (new_packets, int(row["id"]))
                    )

                st.success("Used successfully")
                st.rerun()
            else:
                st.error("Not enough packets")
