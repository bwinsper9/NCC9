
import streamlit as st
import pandas as pd
import random
import time
from fpdf import FPDF
import tempfile

# Load custom style
try:
    st.markdown(open("sexy_minimal_ui_style_snippet.html").read(), unsafe_allow_html=True)
except FileNotFoundError:
    st.warning("UI style sheet not found. Using default styling.")

# App setup
st.set_page_config(page_title="Catering Companion", layout="centered", page_icon="🍴")
affirmations = [
    "You're doing great work, keep pushing.",
    "Today's prep is tomorrow's peace.",
    "Every tray you prep is a step closer to success.",
]

try:
    # Load recipe data
    recipes_df = pd.read_csv("master_recipe_template.csv")

    # Clean up Quantity column and drop problematic rows
    recipes_df = recipes_df.dropna(subset=["Quantity", "BaseServings"])
    recipes_df = recipes_df[pd.to_numeric(recipes_df["Quantity"], errors="coerce").notnull()]
    recipes_df = recipes_df[pd.to_numeric(recipes_df["BaseServings"], errors="coerce").notnull()]

    # Convert to correct types
    recipes_df["Quantity"] = recipes_df["Quantity"].astype(float)
    recipes_df["BaseServings"] = recipes_df["BaseServings"].astype(int)

    available_recipes = sorted(recipes_df["RecipeName"].unique())
    guests = st.number_input("Number of guests", min_value=1, step=1)
    selected = st.multiselect("Select recipes", options=available_recipes)

    if st.button("Generate Plan") and selected and guests > 0:
        st.write("✨ " + random.choice(affirmations))
        time.sleep(1)

        combined_scaled = pd.DataFrame()
        individual_scaled = {}
        methods = {}

        for recipe_name in selected:
            data = recipes_df[recipes_df["RecipeName"].str.lower() == recipe_name.lower()]
            base_servings = data["BaseServings"].iloc[0]
            if base_servings == 0:
                st.error(f"Recipe '{recipe_name}' has BaseServings set to 0. Skipping.")
                continue

            scale_factor = guests / base_servings
            data["ScaledQuantity"] = data["Quantity"] * scale_factor
            combined_scaled = pd.concat([combined_scaled, data], ignore_index=True)
            individual_scaled[recipe_name] = data
            methods[recipe_name] = data["Method"].iloc[0]

        # Combine shopping list
        combined_scaled = combined_scaled.groupby(["Ingredient", "Unit", "Category"], as_index=False).sum()
        sections = {}
        for category, group in combined_scaled.groupby(["Category"]):
            lines = []
            for _, row in group.sort_values("Ingredient").iterrows():
                qty = round(row["ScaledQuantity"], 2)
                if qty.is_integer():
                    qty = int(qty)
                lines.append(f"{qty} {row['Unit']} {row['Ingredient']}")
            sections[category] = lines

        # Prepare recipe guides
        recipe_guides = {}
        for recipe_name, scaled_data in individual_scaled.items():
            ingredients_list = []
            for _, row in scaled_data.iterrows():
                qty = round(row["ScaledQuantity"], 2)
                if qty.is_integer():
                    qty = int(qty)
                ingredients_list.append((qty, row["Unit"], row["Ingredient"]))
            recipe_guides[recipe_name] = (ingredients_list, methods[recipe_name])

        st.markdown("### ✅ Shopping List and Recipe Guides have been generated.")

        st.markdown("## 🛒 Shopping List Preview")
        for i, (category, lines) in enumerate(sections.items()):
            st.markdown(f"### {(category[0] if isinstance(category, tuple) else category).upper()}")
            for j, line in enumerate(lines):
                st.checkbox(line, value=False, key=f"{line}_{i}_{j}")

        st.markdown("---")
        st.markdown("## 📋 Recipe Guides Preview")
        for recipe_name, (ingredients_list, method_text) in recipe_guides.items():
            st.markdown(f"### {recipe_name.upper()}")
            st.markdown("#### Ingredients:")
            for qty, unit, item in ingredients_list:
                st.markdown(f"- {qty} {unit} {item}")
            st.markdown("#### Method:")
            st.markdown(method_text)
            st.markdown("---")

except Exception as e:
    st.error(f"Error loading app: {e}")
