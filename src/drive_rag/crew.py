# src/drive_integration/crew.py
from crewai import Crew, Process
from drive_integration.config.agents import drive_agent
from drive_integration.config.tasks import list_drive_files_task

crew = Crew(
    agents=[drive_agent],
    tasks=[list_drive_files_task],
    process=Process.sequential,
)
