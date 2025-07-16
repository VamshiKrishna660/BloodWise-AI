# Importing libraries and files
from typing import Type
from pydantic import BaseModel, Field
from langchain_community.document_loaders import PyPDFLoader
from crewai.tools import BaseTool
from crewai_tools.tools import SerperDevTool
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()


# Creating search tool
search_tool = SerperDevTool()

class BloodTestReportToolInput(BaseModel):
    path: str = Field(description="Path of the PDF file to read.")


class BloodTestReportTool(BaseTool):
    name: str = "Blood Test Report Reader"
    description: str = "Reads and extracts data from a blood test report PDF."
    args_schema: Type[BaseModel] = BloodTestReportToolInput

    def _run(self, path: str) -> str:
        return asyncio.run(self.read_data_tool(path=path))

    async def read_data_tool(self, path: str) -> str:
        """Tool to read data from a PDF file."""
        docs = PyPDFLoader(file_path=path).load()

        full_report = ""
        for data in docs:
            content = data.page_content
            while "\n\n" in content:
                content = content.replace("\n\n", "\n")
            full_report += content + "\n"

        return full_report

# Creating Nutrition Analysis Tool
# Input schema for NutritionTool
class NutritionToolInput(BaseModel):
    blood_report_data: str = Field(description="Blood report data to analyze.")


class NutritionTool(BaseTool):
    name: str = "Nutrition Analysis Tool"
    description: str = "Analyzes blood report data and provides nutrition recommendations."
    args_schema: Type[BaseModel] = NutritionToolInput

    def _run(self, blood_report_data: str) -> str:
        return asyncio.run(self.analyze_nutrition_tool(blood_report_data=blood_report_data))

    async def analyze_nutrition_tool(self, blood_report_data: str) -> str:
        """Analyze blood report data and provide nutrition recommendations."""
        processed_data = blood_report_data
        i = 0
        while i < len(processed_data):
            if processed_data[i:i+2] == "  ":
                processed_data = processed_data[:i] + processed_data[i+1:]
            else:
                i += 1

        recommendations = []
        data = processed_data.lower()
        if "anemia" in data or "low hemoglobin" in data:
            recommendations.append(
                "Increase intake of iron-rich foods (e.g., spinach, lentils, red meat) and vitamin C to enhance absorption.")
        if "high cholesterol" in data or "cholesterol" in data:
            recommendations.append(
                "Adopt a diet low in saturated fats and cholesterol; increase fiber intake with fruits, vegetables, and whole grains.")
        if "high glucose" in data or "diabetes" in data:
            recommendations.append(
                "Limit simple sugars and refined carbs; focus on whole grains, lean proteins, and plenty of non-starchy vegetables.")
        if "vitamin d" in data or "low vitamin d" in data:
            recommendations.append(
                "Increase vitamin D intake through fortified foods, fatty fish, or supplements as advised by a healthcare provider.")
        if not recommendations:
            recommendations = [
                "Maintain a balanced diet rich in vegetables, fruits, whole grains, and lean proteins.",
                "Stay hydrated and limit processed foods, added sugars, and excess salt.",
                "Consult a registered dietitian for personalized nutrition advice based on your full blood report."
            ]
        return "\n".join(recommendations)

# Creating Exercise Planning Tool
# Input schema for ExerciseTool

class ExerciseToolInput(BaseModel):
    blood_report_data: str = Field(
        description="Blood report data to create an exercise plan.")


class ExerciseTool(BaseTool):
    name: str = "Exercise Planning Tool"
    description: str = "Generates an exercise plan based on blood test data."
    args_schema: Type[BaseModel] = ExerciseToolInput

    def _run(self, blood_report_data: str) -> str:
        return asyncio.run(self.create_exercise_plan_tool(blood_report_data=blood_report_data))

    async def create_exercise_plan_tool(self, blood_report_data: str) -> str:
        """Generate a simple exercise plan based on blood test data."""
        processed_data = blood_report_data
        i = 0
        while i < len(processed_data):
            if processed_data[i:i+2] == "  ":
                processed_data = processed_data[:i] + processed_data[i+1:]
            else:
                i += 1

        recommendations = []
        data = processed_data.lower()
        if "anemia" in data or "low hemoglobin" in data:
            recommendations.append(
                "Include moderate walking or cycling 3-4 times a week to improve stamina, but avoid high-intensity workouts until anemia is resolved.")
        if "high cholesterol" in data or "cholesterol" in data:
            recommendations.append(
                "Incorporate aerobic exercises like brisk walking, swimming, or jogging for at least 150 minutes per week to help manage cholesterol levels.")
        if "high glucose" in data or "diabetes" in data:
            recommendations.append(
                "Add regular aerobic activity and light resistance training to help control blood sugar levels.")
        if "hypertension" in data or "high blood pressure" in data:
            recommendations.append(
                "Practice low-impact exercises such as walking, yoga, or swimming, and avoid heavy weightlifting.")
        if not recommendations:
            recommendations = [
                "Engage in at least 150 minutes of moderate aerobic exercise per week (e.g., brisk walking, cycling).",
                "Include 2 days of light strength training to support overall health.",
                "Incorporate flexibility and balance exercises, such as yoga or stretching, to reduce injury risk."
            ]
        return "\n".join(recommendations)