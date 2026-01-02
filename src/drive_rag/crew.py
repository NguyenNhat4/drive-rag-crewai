# src/drive_integration/crew.py

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from drive_rag.tools.google_drive_list_tool import list_google_drive_files


@CrewBase
class LatestAiDevelopmentCrew():
    """LatestAiDevelopment crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def driveRAG(self) -> Agent:
        return Agent(
            config=self.agents_config['drive_agent'], # type: ignore[index]
            verbose=True,
            tools=[list_google_drive_files]
        )

    @task
    def list_task(self) -> Task:
        return Task(
            config=self.tasks_config['list_drive_files_task'], # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the LatestAiDevelopment crew"""
        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )





