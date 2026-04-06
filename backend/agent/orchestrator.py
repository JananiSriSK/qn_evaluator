import logging
from typing import List

from services.model_registry import model_registry
from services.domain_manager import DomainManager
from services.evaluation_service import EvaluationService
from services.enrichment_service import EnrichmentService
from services.history_service import HistoryService
from services.pdf_parser import PDFQuestionParser
from services.report_generator import ReportGenerator
from services.metrics_service import MetricsService
from services.adaptive_question_service import AdaptiveQuestionService

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Single entry point for all system operations"""

    def __init__(self, mongo_storage):
        self.mongo_storage = mongo_storage
        embedder = model_registry.get_bi_encoder()
        self.domain_manager = DomainManager("data", embedder=embedder, mongo_storage=mongo_storage)
        self.evaluation_service = EvaluationService("data", mongo_storage=mongo_storage)

    def init_history(self, repository):
        self.history_service = HistoryService(repository=repository)

    # ── Domain ────────────────────────────────────────────────────────────────

    def create_domain(self, user_id, domain_name):
        self.mongo_storage.create_domain(user_id, domain_name)

    def list_domains(self, user_id):
        return self.mongo_storage.list_domains(user_id)

    def delete_domain(self, user_id, domain_name):
        self.mongo_storage.delete_domain(user_id, domain_name)

    def get_domain_status(self, user_id, domain_name):
        status = self.mongo_storage.get_domain_status(user_id, domain_name)
        history = self.history_service.get_history(user_id)
        status["evaluated_papers"] = [
            {
                "id": e.get("id"),
                "filename": e.get("filename"),
                "timestamp": e.get("timestamp"),
                "total_questions": e.get("total_questions"),
            }
            for e in history.get("pdf_evaluations", [])
            if e.get("domain_name") == domain_name
        ]
        return status

    # ── Syllabus ──────────────────────────────────────────────────────────────

    def upload_syllabus(self, user_id, domain_name, file_bytes, filename):
        syllabus = self.domain_manager.save_syllabus(user_id, domain_name, file_bytes, filename)
        index_rebuilt = False
        if self.mongo_storage.list_books(user_id, domain_name):
            embedder = model_registry.get_bi_encoder()
            index_rebuilt = self.domain_manager.build_vector_db(user_id, domain_name, embedder)
        return syllabus, index_rebuilt

    def delete_syllabus(self, user_id, domain_name):
        self.mongo_storage.delete_syllabus(user_id, domain_name)

    def view_syllabus(self, user_id, domain_name):
        return self.domain_manager.load_syllabus(user_id, domain_name)

    def get_syllabus_file(self, user_id, domain_name):
        return self.mongo_storage.get_syllabus_file(user_id, domain_name)

    # ── Books ─────────────────────────────────────────────────────────────────

    def upload_books(self, user_id, domain_name, temp_files):
        embedder = model_registry.get_bi_encoder()
        success = self.domain_manager.add_books(user_id, domain_name, temp_files, embedder)
        index, metadata = self.domain_manager.load_index(user_id, domain_name)
        chunks_count = len(metadata) if metadata else 0

        if success:
            syllabus = self.domain_manager.load_syllabus(user_id, domain_name)
            if syllabus and index and metadata:
                try:
                    enrichment = EnrichmentService()
                    cross_encoder = model_registry.get_cross_encoder()
                    enriched = enrichment.enrich_syllabus_data(syllabus, index, metadata, embedder, cross_encoder)
                    self.mongo_storage.save_syllabus(user_id, domain_name, enriched)
                    logger.info("Enrichment completed and saved")
                except Exception as e:
                    logger.warning(f"Enrichment failed (non-critical): {e}")

        return success, chunks_count

    def delete_book(self, user_id, domain_name, book_name):
        self.mongo_storage.delete_book(user_id, domain_name, book_name)
        embedder = model_registry.get_bi_encoder()
        self.domain_manager.build_vector_db(user_id, domain_name, embedder)

    def list_books(self, user_id, domain_name):
        return self.mongo_storage.list_books(user_id, domain_name)

    # ── Index ─────────────────────────────────────────────────────────────────

    def rebuild_index(self, user_id, domain_name):
        embedder = model_registry.get_bi_encoder()
        success = self.domain_manager.build_vector_db(user_id, domain_name, embedder)
        index, metadata = self.domain_manager.load_index(user_id, domain_name)
        chunks_count = len(metadata) if metadata else 0

        if success and index and metadata:
            try:
                enrichment = EnrichmentService()
                cross_encoder = model_registry.get_cross_encoder()
                syllabus = self.domain_manager.load_syllabus(user_id, domain_name)
                if syllabus:
                    enriched = enrichment.enrich_syllabus_data(syllabus, index, metadata, embedder, cross_encoder)
                    self.mongo_storage.save_syllabus(user_id, domain_name, enriched)
            except Exception as e:
                logger.warning(f"Enrichment failed (non-critical): {e}")

        return success, chunks_count

    # ── Evaluation ────────────────────────────────────────────────────────────

    def evaluate_question(self, user_id, domain_name, question):
        result = self.evaluation_service.evaluate_question(user_id, domain_name, question)
        self.history_service.add_single_question(user_id, domain_name, question, result)
        return result

    def evaluate_pdf(self, user_id, domain_name, filename, pdf_bytes):
        text = PDFQuestionParser.extract_text_from_pdf(pdf_bytes)
        questions = PDFQuestionParser.split_questions(text)
        logger.info(f"Extracted {len(questions)} questions from {filename}")

        results = []
        for q in questions:
            try:
                result = self.evaluation_service.evaluate_question(user_id, domain_name, q["text"])
                results.append({
                    "question_number": q["number"],
                    "part": q.get("part", "Part A"),
                    "question": result["question"],
                    "unit": result.get("unit"),
                    "unit_title": result.get("unit_title"),
                    "topic": result.get("topic"),
                    "course_outcomes": result.get("course_outcomes", []),
                    "bloom_level": result["bloom_level"],
                    "bloom_confidence": result["bloom_confidence"],
                    "out_of_syllabus": result.get("out_of_syllabus", False),
                    "subtopics": result.get("subtopics", []),
                    "relevant_chunks": result.get("relevant_chunks", []),
                })
            except Exception as e:
                logger.error(f"Error evaluating question {q['number']}: {e}")
                results.append({
                    "question_number": q["number"],
                    "part": q.get("part", "Part A"),
                    "question": q["text"][:100],
                    "error": str(e),
                })

        eval_id = self.history_service.add_pdf_evaluation(
            user_id, domain_name, filename, len(questions), results
        )
        return eval_id, len(questions), results

    def predict_bloom(self, question):
        return model_registry.predict_bloom(question)

    # ── Report ────────────────────────────────────────────────────────────────

    def generate_report(self, domain_name, results, fmt, report_type, meta=None):
        if fmt == "pdf":
            return ReportGenerator.generate_pdf(domain_name, results, report_type, meta=meta)
        return ReportGenerator.generate_docx(domain_name, results, report_type, meta=meta)

    # ── Metrics ───────────────────────────────────────────────────────────────

    def run_metrics(self, user_id, domain_name, labeled_data):
        svc = MetricsService(self.evaluation_service)
        return svc.run(user_id, domain_name, labeled_data)

    # ── Adaptive Question Generation ──────────────────────────────────────────

    def generate_adaptive_questions(self, results, user_id, domain_name):
        syllabus = self.domain_manager.load_syllabus(user_id, domain_name)
        if not syllabus:
            return {"error": "Syllabus not found"}
        index, metadata = self.domain_manager.load_index(user_id, domain_name)
        embedder = model_registry.get_bi_encoder()
        cross_encoder = model_registry.get_cross_encoder()
        svc = AdaptiveQuestionService()
        return svc.analyze_and_generate(results, syllabus, index, metadata, embedder, cross_encoder)

    # ── History ───────────────────────────────────────────────────────────────

    def get_history(self, user_id):
        return self.history_service.get_history(user_id)

    def delete_single_question(self, user_id, question_id):
        return self.history_service.delete_single_question(user_id, question_id)

    def delete_pdf_evaluation(self, user_id, eval_id):
        return self.history_service.delete_pdf_evaluation(user_id, eval_id)

    def clear_all_history(self, user_id):
        return self.history_service.clear_all_history(user_id)
