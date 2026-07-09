import io
import os
import pandas as pd
import duckdb
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, white
from reportlab.lib.units import inch


class FileProcessor:
    """Handles loading Excel and CSV files into DataFrames"""

    def __init__(self, filename: str, content: bytes):
        self.filename = filename
        self.content = content

    def load(self) -> pd.DataFrame:
        if self.filename.endswith(".csv"):
            return pd.read_csv(io.BytesIO(self.content))
        else:
            return pd.read_excel(io.BytesIO(self.content))


class DataCleaner:
    """Handles all data cleaning operations on a single DataFrame"""

    def __init__(self, filename: str, df: pd.DataFrame):
        self.filename = filename
        self.df = df.copy()
        self.logs = []

    def remove_duplicates(self):
        before = len(self.df)
        self.df = self.df.drop_duplicates()
        removed = before - len(self.df)
        if removed > 0:
            self.logs.append(f"{self.filename}: Removed {removed} duplicate rows")
        return self

    def fix_missing_values(self):
        for col in self.df.columns:
            missing = self.df[col].isna().sum()
            if missing > 0:
                if self.df[col].dtype in ["float64", "int64"]:
                    self.df[col] = self.df[col].fillna(0)
                    self.logs.append(f"{self.filename}: Filled {missing} missing numeric values in '{col}' with 0")
                else:
                    self.df[col] = self.df[col].fillna("Unknown")
                    self.logs.append(f"{self.filename}: Filled {missing} missing text values in '{col}' with 'Unknown'")
        return self

    def standardize_dates(self):
        for col in self.df.columns:
            if "date" in col.lower():
                try:
                    self.df[col] = pd.to_datetime(self.df[col], dayfirst=True).dt.strftime("%Y-%m-%d")
                    self.logs.append(f"{self.filename}: Standardized date column '{col}' to YYYY-MM-DD format")
                except Exception:
                    pass
        return self

    def strip_whitespace(self):
        for col in self.df.select_dtypes(include="object").columns:
            self.df[col] = self.df[col].astype(str).str.strip()
        self.logs.append(f"{self.filename}: Stripped whitespace from all text columns")
        return self

    def clean(self):
        self.remove_duplicates()
        self.fix_missing_values()
        self.standardize_dates()
        self.strip_whitespace()
        self.logs.append(f"{self.filename}: Cleaning complete — {len(self.df)} rows remaining")
        return self.df, self.logs


class DataMerger:
    """Handles merging multiple cleaned DataFrames into one consolidated file"""

    COLUMN_MAP = {
        "Item Code": "Product ID",
        "SKU": "Product ID",
        "Material ID": "Product ID",
        "Product Code": "Product ID",
        "Supplier Name": "Vendor",
        "Invoice No": "Invoice Number",
        "Purchase Price": "Unit Cost",
        "Sale Price": "Selling Price",
        "Units Sold": "Quantity Sold",
        "Stock Quantity": "Stock",
        "Last Updated": "Date",
        "Purchase Date": "Date",
        "Sale Date": "Date",
    }

    def __init__(self, dataframes: dict):
        self.dataframes = dataframes
        self.logs = []

    def standardize_columns(self, df: pd.DataFrame, filename: str) -> pd.DataFrame:
        renamed = {}
        for col in df.columns:
            if col in self.COLUMN_MAP:
                renamed[col] = self.COLUMN_MAP[col]
        if renamed:
            df = df.rename(columns=renamed)
            self.logs.append(f"{filename}: Renamed columns {renamed}")
        return df

    def merge(self):
        standardized = {}
        for filename, df in self.dataframes.items():
            standardized[filename] = self.standardize_columns(df, filename)

        all_dfs = []
        for filename, df in standardized.items():
            df["Source File"] = filename
            all_dfs.append(df)

        consolidated = pd.concat(all_dfs, ignore_index=True, sort=False)
        self.logs.append(f"Merged {len(self.dataframes)} files into one consolidated DataFrame")
        self.logs.append(f"Final consolidated data: {len(consolidated)} rows, {len(consolidated.columns)} columns")
        self.logs.append(f"Final columns: {list(consolidated.columns)}")

        return consolidated, self.logs


class ReportGenerator:
    """Generates a PDF audit report of all transformations"""

    def __init__(self, audit_log: list, consolidated_df):
        self.audit_log = audit_log
        self.consolidated_df = consolidated_df

    def generate(self) -> str:
        os.makedirs("output", exist_ok=True)
        path = "output/audit_report.pdf"

        doc = SimpleDocTemplate(path, pagesize=letter,
                                rightMargin=0.75*inch, leftMargin=0.75*inch,
                                topMargin=0.75*inch, bottomMargin=0.75*inch)

        BLUE = HexColor("#2C5282")
        GRAY = HexColor("#718096")
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle("Title", fontSize=22, textColor=BLUE,
                                     fontName="Helvetica-Bold", spaceAfter=6)
        h2_style = ParagraphStyle("H2", fontSize=14, textColor=BLUE,
                                  fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=6)
        body_style = ParagraphStyle("Body", fontSize=10, fontName="Helvetica",
                                    spaceAfter=6, leading=15)
        log_style = ParagraphStyle("Log", fontSize=9, fontName="Courier",
                                   spaceAfter=4, leading=13, leftIndent=10,
                                   textColor=HexColor("#2D3748"))

        story = []

        story.append(Paragraph("Excel Consolidator — Audit Report", title_style))
        story.append(Paragraph("Auto-generated report of all data transformations", 
                               ParagraphStyle("Sub", fontSize=11, textColor=GRAY, 
                                              fontName="Helvetica", spaceAfter=16)))
        story.append(HRFlowable(width="100%", thickness=1, 
                                color=HexColor("#E2E8F0"), spaceAfter=12))

        story.append(Paragraph("Transformation Log", h2_style))
        story.append(Paragraph("Every step performed on your data, in order:", body_style))
        story.append(Spacer(1, 6))

        for i, log in enumerate(self.audit_log, 1):
            story.append(Paragraph(f"{i}. {log}", log_style))

        if self.consolidated_df is not None:
            story.append(Spacer(1, 16))
            story.append(HRFlowable(width="100%", thickness=1,
                                    color=HexColor("#E2E8F0"), spaceAfter=12))
            story.append(Paragraph("Consolidated Data Summary", h2_style))

            summary_data = [
                ["Metric", "Value"],
                ["Total Rows", str(len(self.consolidated_df))],
                ["Total Columns", str(len(self.consolidated_df.columns))],
                ["Columns", ", ".join(list(self.consolidated_df.columns))],
            ]

            table = Table(summary_data, colWidths=[2*inch, 4.5*inch])
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), BLUE),
                ("TEXTCOLOR", (0, 0), (-1, 0), white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), 
                 [HexColor("#F7FAFC"), white]),
                ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#E2E8F0")),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(table)

            story.append(Spacer(1, 16))
            story.append(Paragraph("Data Preview (first 10 rows)", h2_style))

            preview = self.consolidated_df.head(10).fillna("").astype(str)
            preview_data = [list(preview.columns)] + preview.values.tolist()

            col_count = len(preview.columns)
            col_width = 6.5*inch / col_count

            preview_table = Table(preview_data, colWidths=[col_width] * col_count)
            preview_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), BLUE),
                ("TEXTCOLOR", (0, 0), (-1, 0), white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                 [HexColor("#F7FAFC"), white]),
                ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#E2E8F0")),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(preview_table)

        doc.build(story)
        return path