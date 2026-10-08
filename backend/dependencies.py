import os
from typing import Generator
from core.storage.store import InMemoryStore
from core.services.graph_service import GraphService
from core.services.assessment_service import AssessmentService
from core.services.knowledge_service import KnowledgeStateEngine
from core.services.gap_analyzer import GapAnalyzer
from core.services.recommender import RecommendationEngine
from core.services.roadmap_engine import RoadmapEngine
from core.services.adaptation_engine import AdaptationEngine
from core.services.llm_service import LLMService

class ServiceContainer:
    """
    Centralized container managing singleton instances of all core domain services
    and the authoritative InMemoryStore.
    """
    def __init__(self):
        self.store = InMemoryStore()
        self.graph_service = GraphService(data_dir="data/skills")
        self.assessment_service = AssessmentService(data_path="data/assessment/assessment_bank.json")
        self.knowledge_engine = KnowledgeStateEngine(assessment_service=self.assessment_service)
        self.gap_analyzer = GapAnalyzer(graph_service=self.graph_service)
        self.recommender = RecommendationEngine(catalog_path="data/resources/resources_catalog.json")
        self.roadmap_engine = RoadmapEngine(graph_service=self.graph_service, recommender=self.recommender)
        self.adaptation_engine = AdaptationEngine(
            gap_analyzer=self.gap_analyzer,
            roadmap_engine=self.roadmap_engine,
            recommender=self.recommender
        )
        self.llm_service = LLMService()

# Global Singleton Container
_container: ServiceContainer = None

def get_container() -> ServiceContainer:
    global _container
    if _container is None:
        _container = ServiceContainer()
    return _container

def get_store() -> InMemoryStore:
    return get_container().store

def get_graph_service() -> GraphService:
    return get_container().graph_service

def get_assessment_service() -> AssessmentService:
    return get_container().assessment_service

def get_knowledge_engine() -> KnowledgeStateEngine:
    return get_container().knowledge_engine

def get_gap_analyzer() -> GapAnalyzer:
    return get_container().gap_analyzer

def get_recommender() -> RecommendationEngine:
    return get_container().recommender

def get_roadmap_engine() -> RoadmapEngine:
    return get_container().roadmap_engine

def get_adaptation_engine() -> AdaptationEngine:
    return get_container().adaptation_engine

def get_llm_service() -> LLMService:
    return get_container().llm_service
