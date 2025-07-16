# Importing libraries and files
from agents import *
from tools import *

from crewai import Crew, Process, Task
from agents import verifier, doctor, nutritionist, exercise_specialist
import os
import logging

logger = logging.getLogger(__name__)


# Creating a task to help solve user's query
help_patients = Task(
    description="""Analyze the user's query: "{query}" and the blood test report located at "{file_path}". \
                    Use evidence-based medical knowledge to identify any abnormalities, provide a clear summary, and offer actionable health recommendations. \
                    Use the Blood Test Report Reader tool to read the file at the given path. \
                    If relevant, search the internet for recent guidelines or studies. Always prioritize patient safety and clarity in your response.""",
    expected_output="""1. List any detected abnormalities or notable findings from the blood test (with reference ranges if possible).
                        2. Provide a concise summary of the patient's likely health status.
                        3. Offer 2-3 evidence-based medical recommendations tailored to the findings.
                        4. If appropriate, include up to 3 reputable medical website URLs for further reading.
                        5. Use clear, non-alarming language and avoid unnecessary jargon.""",
    agent=doctor,
    tools=[BloodTestReportTool(), search_tool],
    async_execution=False,
)

# Creating a nutrition analysis task
nutrition_analysis = Task(
    description="""Review the patient's blood test report located at "{file_path}" and provide a detailed nutrition analysis. \
Use the Blood Test Report Reader tool to read the file. \
Identify any deficiencies or health risks, and recommend at least 3 evidence-based dietary changes or supplements. \
Explain the reasoning behind each recommendation and reference relevant blood markers.""",
    expected_output="""1. List any blood markers related to nutrition that are outside the normal range (e.g., iron, cholesterol, glucose, vitamin D).
2. For each finding, provide a specific dietary or supplement recommendation, with a brief explanation.
3. Include at least 3 actionable nutrition tips, and reference reputable sources if possible.
4. Avoid recommending unnecessary or unproven supplements.""",
    agent=nutritionist,
    tools=[BloodTestReportTool(), NutritionTool()],
    async_execution=False,
)

# Creating an exercise planning task
exercise_planning = Task(
    description="""Design a safe, effective exercise plan based on the patient's blood test results from "{file_path}" and current health status. \
Use the Blood Test Report Reader tool to read the file. \
Take into account any medical conditions or limitations, and provide at least 3 specific exercise recommendations. \
Explain the rationale for each recommendation and ensure all advice is medically appropriate.""",
    expected_output="""1. Summarize any blood test findings relevant to exercise planning (e.g., anemia, high cholesterol, glucose levels).
2. Provide a structured exercise plan with at least 3 components (aerobic, strength, flexibility/balance).
3. For each component, specify frequency, intensity, and duration (e.g., 150 min/week moderate aerobic activity).
4. Include safety precautions and reference clinical guidelines if possible.""",
    agent=exercise_specialist,
    tools=[BloodTestReportTool(), ExerciseTool()],
    async_execution=False,
)


verification = Task(
    description="""Carefully verify the uploaded document at "{file_path}" to confirm it is a legitimate, complete blood test report. \
Use the Blood Test Report Reader tool to read the file. \
Check for the presence of at least 10 key blood markers, and flag any missing or suspicious data. \
Ensure the report is suitable for clinical analysis and patient care.""",
    expected_output="""1. State whether the document is a valid blood test report (yes/no).
2. List the key blood markers found (up to 10).
3. Note any missing or suspicious elements.
4. Provide a brief summary of the report's completeness and reliability.""",
    agent=verifier,
    tools=[BloodTestReportTool()],
    async_execution=False
)