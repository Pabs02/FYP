import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

try:
	from openai import OpenAI
except ImportError:
	OpenAI = None


class ChatGPTClientError(Exception):
	"""Raised when the OpenAI configuration or response is invalid."""


@dataclass
class BreakdownItem:
	sequence: int
	title: str
	description: str
	estimated_hours: Optional[float]
	planned_start: Optional[str] = None
	planned_end: Optional[str] = None
	focus: Optional[str] = None


@dataclass
class BreakdownResponse:
	subtasks: List[BreakdownItem]
	advice: Optional[str]
	raw_text: str


@dataclass
class AssignmentReviewResponse:
	feedback: str
	score_estimate: Optional[float]
	possible_score: Optional[float]
	strengths: List[str]
	weaknesses: List[str]
	suggestions: List[str]
	raw_text: str


@dataclass
class CourseBotCitation:
	source: str
	quote: str


@dataclass
class CourseBotResponse:
	answer: str
	citations: List[CourseBotCitation]
	raw_text: str


@dataclass
class AssignmentReviewResponse:
	feedback: str
	score_estimate: Optional[float]
	possible_score: Optional[float]
	strengths: List[str]
	weaknesses: List[str]
	suggestions: List[str]
	raw_text: str


DEFAULT_MODEL_NAME = "gpt-4o-mini"


class ChatGPTTaskBreakdownService:
	"""Wrapper around OpenAI ChatGPT for producing task micro-plan suggestions."""

	def __init__(self, api_key: str, model_name: str = DEFAULT_MODEL_NAME):
		if not api_key:
			raise ChatGPTClientError("Missing OpenAI API key.")
		if OpenAI is None:
			raise ChatGPTClientError("openai package is not installed. Run `pip install openai`.")

		self._model_name = model_name or DEFAULT_MODEL_NAME
		try:
			self._client = OpenAI(api_key=api_key)
		except Exception as exc:  # pragma: no cover - external dependency
			raise ChatGPTClientError(f"Failed to initialise OpenAI client: {exc}") from exc

	def breakdown_task(
		self,
		*,
		task_title: str,
		module_code: Optional[str],
		due_date: Optional[str],
		due_at: Optional[str],
		status: Optional[str],
		description: Optional[str],
		additional_context: Optional[str],
		schedule_context: Optional[str]
	) -> BreakdownResponse:
		if not task_title:
			raise ChatGPTClientError("Task title is required for AI breakdown.")

		system_prompt, user_prompt = self._build_prompts(
			task_title=task_title,
			module_code=module_code,
			due_date=due_date,
			due_at=due_at,
			status=status,
			description=description,
			additional_context=additional_context,
			schedule_context=schedule_context,
		)

		response = self._client.responses.create(
			model=self._model_name,
			input=[
				{"role": "system", "content": system_prompt},
				{"role": "user", "content": user_prompt},
			],
			temperature=0.4,
			max_output_tokens=2500,  #  to support 8-12 detailed subtasks
		)

		text = self._extract_text(response)
		payload = self._parse_json(text)
		items = self._normalise_items(payload.get("subtasks", []))
		advice = self._safe_str(payload.get("advice"))
		return BreakdownResponse(subtasks=items, advice=advice, raw_text=text)

	def review_and_grade_assignment(
		self,
		*,
		assignment_text: str,
		task_title: str,
		assignment_brief: Optional[str] = None
	) -> AssignmentReviewResponse:
		# Reference: ChatGPT (OpenAI) - Assignment Review Prompt Design
		# Date: 2026-01-22
		# Prompt: "I need a strict JSON schema for assignment feedback, strengths, weaknesses,
		# and suggestions. Can you help me craft the system/user prompts?"
		# ChatGPT provided the grading prompt and JSON schema guidance.
		"""
		Review and grade an assignment draft.
		Returns feedback, score estimate, strengths, weaknesses, and suggestions.
		"""
		system_prompt = (
			"You are a \"hyper critical\" academic assessor and writing tutor. "
			"Review student assignments and provide rigorous, detailed feedback. "
			"Be demanding and identify gaps, weaknesses, and missing evidence with concrete examples. "
			"Offer actionable, high-standard suggestions for improvement. "
			"Be thorough and specific, but do not be insulting. "
			"Apply strict scoring and do not inflate marks; penalize unclear arguments, weak evidence, "
			"and poor structure more heavily than a typical assessor. "
			"Use conservative grade bands: <50 poor, 50–59 weak, 60–69 adequate, 70–79 good, "
			"80–89 excellent (rare), 90+ outstanding (exceptional). "
			"Scores above 80 should be rare and only when there are virtually no meaningful weaknesses "
			"and the work shows outstanding evidence, structure, originality, and academic rigor."
		)

		user_prompt_lines = [
			"Review the following assignment submission and provide comprehensive, detailed feedback.",
			"",
			f"Assignment Title: {task_title}",
			"",
		]

		if assignment_brief:
			user_prompt_lines.extend([
				"Assignment Brief / Rubric / Requirements:",
				assignment_brief,
				"",
			])

		user_prompt_lines.extend([
			"Assignment Content:",
			assignment_text,
			"",
			"Use a harsh grading standard. Default to lower scores unless the work is exceptional.",
			"If you list multiple Areas for Improvement, the score should reflect that and stay in a lower band.",
			"Do NOT reuse or anchor to past scores; judge only the content provided here.",
			"Return ONLY JSON in this exact schema:",
			"{",
			'  "feedback": str,  // Overall detailed feedback (7-10 sentences, be specific and thorough)',
			'  "score_estimate": number,  // Estimated score out of 100 (not displayed to user, but used internally)',
			'  "possible_score": 100,  // Maximum possible score',
			'  "strengths": [str, ...],  // List of 5-7 detailed strengths with specific examples',
			'  "weaknesses": [str, ...],  // List of 5-7 detailed areas for improvement with specific examples',
			'  "suggestions": [str, ...]  // List of 5-7 detailed, actionable suggestions',
			"}",
		])

		user_prompt = "\n".join(user_prompt_lines)

		try:
			response = self._client.responses.create(
				model=self._model_name,
				input=[
					{"role": "system", "content": system_prompt},
					{"role": "user", "content": user_prompt},
				],
				temperature=0.0,
				max_output_tokens=3000,
			)

			text = self._extract_text(response)
			payload = self._parse_json(text)

			feedback = self._safe_str(payload.get("feedback")) or "No feedback provided."
			score_est = payload.get("score_estimate")
			if isinstance(score_est, (int, float)):
				score_est = float(score_est)
			elif isinstance(score_est, str):
				try:
					score_est = float(score_est)
				except ValueError:
					score_est = None
			else:
				score_est = None

			possible = payload.get("possible_score") or 100.0
			if isinstance(possible, (int, float)):
				possible = float(possible)
			else:
				possible = 100.0

			strengths = [self._safe_str(s) for s in payload.get("strengths", []) if self._safe_str(s)]
			weaknesses = [self._safe_str(w) for w in payload.get("weaknesses", []) if self._safe_str(w)]
			suggestions = [self._safe_str(s) for s in payload.get("suggestions", []) if self._safe_str(s)]


			return AssignmentReviewResponse(
				feedback=feedback,
				score_estimate=score_est,
				possible_score=possible,
				strengths=strengths,
				weaknesses=weaknesses,
				suggestions=suggestions,
				raw_text=text
			)
		except Exception as exc:
			raise ChatGPTClientError(f"Failed to review assignment: {exc}") from exc

	def answer_course_question(
		self,
		*,
		question: str,
		sources: List[Dict[str, str]]
	) -> CourseBotResponse:
		# Reference: ChatGPT (OpenAI) - Course Bot Prompt Engineering with Citations
		# Date: 2026-01-14
		# Prompt: "I need a prompt for a course assistant that answers questions using only
		# provided sources and returns JSON with an answer and citations including quotes.
		# Can you design a prompt schema and guidance for this?"
		if not question:
			raise ChatGPTClientError("Question is required.")
		if not sources:
			raise ChatGPTClientError("No course materials were provided.")

		system_prompt = (
			"You are a helpful course assistant. "
			"Answer questions strictly using the provided source materials. "
			"If the answer is not clearly supported by the sources, say you cannot find it in the materials. "
			"Provide concise citations with direct quotes from the sources."
		)

		mcq_mode = any(
			keyword in question.lower()
			for keyword in ("mcq", "multiple choice", "quiz", "test me", "practice questions")
		)
		summary_mode = any(
			keyword in question.lower()
			for keyword in ("summary", "summarise", "summarize", "key points")
		)
		argument_mode = any(
			keyword in question.lower()
			for keyword in ("counter-argument", "counter argument", "counterarguments", "counter arguments", "main arguments")
		)
		flashcard_mode = "flashcard" in question.lower()
		true_false_mode = any(
			keyword in question.lower()
			for keyword in ("true/false", "true or false", "true false", "t/f")
		)

		source_blocks = []
		for item in sources:
			source_name = item.get("source") or "Unknown Source"
			content = item.get("content") or ""
			source_blocks.append(f"Source: {source_name}\nContent:\n{content}")

		if mcq_mode:
			user_prompt_lines = [
				"Use ONLY the sources below to create a short practice quiz.",
				"Create 10-20 multiple choice questions based on the materials.",
				"Each question must have 4 options (A-D) and a clearly indicated correct answer.",
				"Distribute correct answers evenly across A, B, C, and D (avoid repeating the same letter).",
				"Keep the questions focused on key concepts and definitions from the sources.",
				"",
				f"Question: {question}",
				"",
				"Sources:",
				"\n\n".join(source_blocks),
				"",
				"Return ONLY JSON in this exact schema:",
				"{",
				'  "answer": str,  // The full MCQ list in plain text',
				'  "citations": [',
				'    { "source": str, "quote": str }  // Short quotes (<= 200 chars) from sources',
				"  ]",
				"}",
			]
		elif flashcard_mode:
			user_prompt_lines = [
				"Use ONLY the sources below to create flashcards.",
				"Create exactly 20 flashcards.",
				"Return 20 bullet points, each on its own line, using this format:",
				"- Term: <term> | Definition: <definition>",
				"Keep definitions concise but specific (1-2 sentences).",
				"",
				f"Question: {question}",
				"",
				"Sources:",
				"\n\n".join(source_blocks),
				"",
				"Return ONLY JSON in this exact schema:",
				"{",
				'  "answer": str,  // Bullet list of flashcards',
				'  "citations": [',
				'    { "source": str, "quote": str }  // Short quotes (<= 200 chars) from sources',
				"  ]",
				"}",
			]
		elif true_false_mode:
			user_prompt_lines = [
				"Use ONLY the sources below to create true/false questions.",
				"Create exactly 10 questions.",
				"Each line must include the question, the correct answer, and a brief explanation.",
				"Format each line like this:",
				"- Q: <question> | Answer: True/False | Explanation: <1-2 sentences>",
				"Return plain text lines only. Do NOT return Python lists or JSON arrays inside the answer.",
				"",
				f"Question: {question}",
				"",
				"Sources:",
				"\n\n".join(source_blocks),
				"",
				"Return ONLY JSON in this exact schema:",
				"{",
				'  "answer": str,  // 10-line list of true/false questions',
				'  "citations": [',
				'    { "source": str, "quote": str }  // Short quotes (<= 200 chars) from sources',
				"  ]",
				"}",
			]
		elif summary_mode:
			user_prompt_lines = [
				"Use ONLY the sources below to produce a detailed summary.",
				"Write 10-14 bullet points, each 2-3 sentences long.",
				"Each bullet must include a specific detail from the sources and avoid vague wording.",
				"",
				f"Question: {question}",
				"",
				"Sources:",
				"\n\n".join(source_blocks),
				"",
				"Return ONLY JSON in this exact schema:",
				"{",
				'  "answer": str,  // Detailed bullet-point summary grounded in sources',
				'  "citations": [',
				'    { "source": str, "quote": str }  // Short quotes (<= 200 chars) from sources',
				"  ]",
				"}",
			]
		elif argument_mode:
			user_prompt_lines = [
				"Use ONLY the sources below to provide a detailed analysis of arguments and counter-arguments.",
				"Format the answer with two labeled sections: 'Arguments' and 'Counter-Arguments'.",
				"Provide 4-6 bullet points per section, each 2-3 sentences long.",
				"Each bullet must cite a specific detail or claim from the sources.",
				"",
				f"Question: {question}",
				"",
				"Sources:",
				"\n\n".join(source_blocks),
				"",
				"Return ONLY JSON in this exact schema:",
				"{",
				'  "answer": str,  // Detailed arguments and counter-arguments grounded in sources',
				'  "citations": [',
				'    { "source": str, "quote": str }  // Short quotes (<= 200 chars) from sources',
				"  ]",
				"}",
			]
		else:
			user_prompt_lines = [
				"Use ONLY the sources below to answer the question.",
				"",
				f"Question: {question}",
				"",
				"Sources:",
				"\n\n".join(source_blocks),
				"",
				"Return ONLY JSON in this exact schema:",
				"Ensure the JSON is valid and do not wrap it in markdown.",
				"{",
				'  "answer": str,  // Direct answer grounded in the sources',
				'  "citations": [',
				'    { "source": str, "quote": str }  // Short quotes (<= 200 chars) from sources',
				"  ]",
				"}",
			]

		user_prompt = "\n".join(user_prompt_lines)

		try:
			response = self._client.responses.create(
				model=self._model_name,
				input=[
					{"role": "system", "content": system_prompt},
					{"role": "user", "content": user_prompt},
				],
				temperature=0.2,
				max_output_tokens=2800,
			)

			text = self._extract_text(response)
			try:
				payload = self._parse_json(text)
			except ChatGPTClientError:
				# Fall back to raw text if JSON is not returned
				return CourseBotResponse(answer=text.strip(), citations=[], raw_text=text)

			answer = self._safe_str(payload.get("answer")) or "I could not find an answer in the provided materials."
			raw_citations = payload.get("citations", []) or []
			citations: List[CourseBotCitation] = []
			if isinstance(raw_citations, list):
				for entry in raw_citations:
					if not isinstance(entry, dict):
						continue
					source = self._safe_str(entry.get("source")) or "Unknown Source"
					quote = self._safe_str(entry.get("quote")) or ""
					citations.append(CourseBotCitation(source=source, quote=quote))

			return CourseBotResponse(answer=answer, citations=citations, raw_text=text)
		except Exception as exc:
			raise ChatGPTClientError(f"Failed to answer course question: {exc}") from exc

	def review_and_grade_assignment(
		self,
		*,
		assignment_text: str,
		task_title: str,
		assignment_brief: Optional[str] = None
	) -> AssignmentReviewResponse:
		"""
		Review and grade an assignment draft.
		Returns feedback, score estimate, strengths, weaknesses, and suggestions.
		"""
		system_prompt = (
			"You are an experienced academic assessor and writing tutor. "
			"Review student assignments and provide detailed, constructive feedback. "
			"Identify specific strengths and weaknesses with concrete examples, and offer actionable suggestions. "
			"Be thorough, specific, and encouraging. Provide detailed feedback that helps students improve their work."
		)

		user_prompt_lines = [
			"Review the following assignment submission and provide comprehensive, detailed feedback.",
			"",
			f"Assignment Title: {task_title}",
			"",
		]

		if assignment_brief:
			user_prompt_lines.extend([
				"Assignment Brief / Rubric / Requirements:",
				assignment_brief,
				"",
			])

		user_prompt_lines.extend([
			"Assignment Content:",
			assignment_text,
			"",
			"Return ONLY JSON in this exact schema:",
			"{",
			'  "feedback": str,  // Overall detailed feedback (7-10 sentences, be specific and thorough)',
			'  "score_estimate": number,  // Estimated score out of 100 (not displayed to user, but used internally)',
			'  "possible_score": 100,  // Maximum possible score',
			'  "strengths": [str, ...],  // List of 5-7 detailed strengths with specific examples',
			'  "weaknesses": [str, ...],  // List of 5-7 detailed areas for improvement with specific examples',
			'  "suggestions": [str, ...]  // List of 5-7 detailed, actionable suggestions',
			"}",
		])

		user_prompt = "\n".join(user_prompt_lines)

		try:
			response = self._client.responses.create(
				model=self._model_name,
				input=[
					{"role": "system", "content": system_prompt},
					{"role": "user", "content": user_prompt},
				],
				temperature=0.3,
				max_output_tokens=3000,
			)

			text = self._extract_text(response)
			payload = self._parse_json(text)

			feedback = self._safe_str(payload.get("feedback")) or "No feedback provided."
			score_est = payload.get("score_estimate")
			if isinstance(score_est, (int, float)):
				score_est = float(score_est)
			elif isinstance(score_est, str):
				try:
					score_est = float(score_est)
				except ValueError:
					score_est = None
			else:
				score_est = None

			possible = payload.get("possible_score") or 100.0
			if isinstance(possible, (int, float)):
				possible = float(possible)
			else:
				possible = 100.0

			strengths = [self._safe_str(s) for s in payload.get("strengths", []) if self._safe_str(s)]
			weaknesses = [self._safe_str(w) for w in payload.get("weaknesses", []) if self._safe_str(w)]
			suggestions = [self._safe_str(s) for s in payload.get("suggestions", []) if self._safe_str(s)]

			# Reference: ChatGPT (OpenAI) - Scoring Adjustment from Critique Counts
			# Date: 2026-01-22
			# Prompt: "The grading feels too lenient. Can you suggest a way to
			# reduce the score based on the number of weaknesses/suggestions?"
			# ChatGPT provided the adjustment pattern based on critique counts.
			# Apply a stricter scoring adjustment based on the amount of critique.
			if isinstance(score_est, (int, float)):
				deduction = (len(weaknesses) * 2.0) + (len(suggestions) * 1.0)
				if weaknesses or suggestions:
					deduction += 5.0
				score_est = max(0.0, min(100.0, float(score_est) - deduction))

			return AssignmentReviewResponse(
				feedback=feedback,
				score_estimate=score_est,
				possible_score=possible,
				strengths=strengths,
				weaknesses=weaknesses,
				suggestions=suggestions,
				raw_text=text
			)
		except Exception as exc:
			raise ChatGPTClientError(f"Failed to review assignment: {exc}") from exc

	def draft_lecturer_email(
		self,
		*,
		student_name: str,
		student_id: int,
		lecturer_name: Optional[str],
		subject: str,
		request_text: str
	) -> str:
		# Reference: ChatGPT (OpenAI) - Professional Lecturer Email Draft
		# Date: 2026-01-23
		# Prompt: "I need a professional email draft to a lecturer based on a subject
		# and a short request from a student. It should be polite, concise, and sign off
		# with the student's name and ID. Can you craft the prompt?"
		# ChatGPT provided the drafting prompt and format.
		if not subject or not request_text:
			raise ChatGPTClientError("Subject and request details are required.")
		lecturer_label = lecturer_name or "Lecturer"
		system_prompt = (
			"You are a professional academic writing assistant. "
			"Draft clear, polite emails to lecturers. Keep them concise and respectful."
		)
		user_prompt = (
			f"Write a professional email to {lecturer_label}.\n"
			f"Subject: {subject}\n"
			f"Request: {request_text}\n\n"
			"Requirements:\n"
			"- Keep it concise (6-10 sentences).\n"
			"- Be polite and professional.\n"
			"- Include a clear ask.\n"
			f"- Sign off with: Regards, {student_name} (Student ID: {student_id}).\n"
			"- Output plain text only."
		)
		try:
			response = self._client.responses.create(
				model=self._model_name,
				input=[
					{"role": "system", "content": system_prompt},
					{"role": "user", "content": user_prompt},
				],
				temperature=0.3,
				max_output_tokens=600,
			)
			text = self._extract_text(response)
			return self._clean_markdown(text)
		except Exception as exc:
			raise ChatGPTClientError(f"Failed to draft lecturer email: {exc}") from exc

	def _build_prompts(
		self,
		*,
		task_title: str,
		module_code: Optional[str],
		due_date: Optional[str],
		due_at: Optional[str],
		status: Optional[str],
		description: Optional[str],
		additional_context: Optional[str],
		schedule_context: Optional[str],
	) -> (str, str):
		system_prompt = (
			"You are an experienced academic coach and study strategist. "
			"Produce realistic schedules that respect the student's existing commitments. "
			"Break down assignments into granular, actionable micro-tasks with detailed step-by-step guidance and practical ideas. "
			"Each micro-task should be comprehensive enough that a student knows exactly what to do, why they're doing it, and has specific ideas to get started."
		)

		lines = [
			"Break the assignment into 8-12 practical micro-tasks ordered by sequence.",
			"Each micro-task should be focused and achievable in 1-3 hours (prefer shorter, more frequent tasks over long sessions).",
			"Each micro-task must include:",
			"  - A detailed description (3-5 sentences) with specific actionable steps explaining what to do and how to approach it",
			"  - Concrete ideas and suggestions for completing the task (specific resources, methods, or approaches)",
			"  - A recommended focus tip or strategy",
			"  - Estimated hours (aim for 1-3 hours per task, with most tasks around 1.5-2 hours)",
			"  - A suggested start/end window (use plain language such as 'Thu 14 Nov evening' if precise times are unknown)",
			"Make descriptions comprehensive enough that a student knows exactly what to do, why they're doing it, and has practical ideas to get started.",
			"Include specific examples, resources to consult, or methods to use in the descriptions.",
			"Respect the student's existing assignments and events when proposing dates—avoid overlaps.",
			"Return ONLY JSON in this exact schema:",
			"{",
			'  "subtasks": [',
			'    { "sequence": int, "title": str, "description": str, "estimated_hours": number, '
			'"planned_start": str, "planned_end": str, "focus": str }',
			"  ],",
			'  "advice": str  // include a mini study strategy summary (3-4 sentences)',
			"}",
			f"Task title: {task_title}",
		]

		if module_code:
			lines.append(f"Module: {module_code}")
		if status:
			lines.append(f"Current status: {status}")
		if due_date:
			lines.append(f"Due date: {due_date}")
		if due_at:
			lines.append(f"Due at: {due_at}")
		if description:
			lines.append(f"Assignment brief: {description}")
		if additional_context:
			lines.append(f"Additional context: {additional_context}")
		if schedule_context:
			lines.append("")
			lines.append("Student schedule snapshot:")
			lines.append(schedule_context)

		lines.append("")
		lines.append(
			"Ensure the JSON parses in Python. Use concise ISO-like text for planned_start/planned_end (e.g. '2025-11-14 evening'). "
			"Each description should be 3-5 sentences with actionable steps, specific ideas, resources, or methods. "
			"Aim for 8-12 subtasks total, each taking 1-3 hours."
		)
		return system_prompt, "\n".join(lines)

	# Reference: ChatGPT (OpenAI) - OpenAI Response Text Extraction
	# Date: 2025-11-14
	# Prompt: "The OpenAI Responses API returns nested response objects. I need to extract 
	# the text content from response.output[].content[].text. But the API structure might 
	# change, so I need a fallback to response.text if the nested structure isn't available. 
	# Can you help me write robust text extraction with fallbacks?"
	# ChatGPT provided the text extraction logic that navigates the nested response structure 
	# (response.output -> segment.content -> part.text) with fallback to direct .text 
	# attribute. This handles API variations and ensures text is extracted reliably even 
	# when the response format changes.
	def _extract_text(self, response: Any) -> str:
		if response is None:
			raise ChatGPTClientError("OpenAI response was empty.")

		# New Responses API
		output = getattr(response, "output", None)
		if output:
			for segment in output:
				content = getattr(segment, "content", None)
				if not content:
					continue
				for part in content:
					text = getattr(part, "text", None)
					if text:
						return text.strip()

		# Fallback for potential .text attribute
		text_attr = getattr(response, "text", None)
		if isinstance(text_attr, str) and text_attr.strip():
			return text_attr.strip()

		raise ChatGPTClientError("OpenAI replied without usable text. Try shortening the brief and retry.")

	# Reference: ChatGPT (OpenAI) - Robust JSON Parsing with Fallbacks
	# Date: 2025-11-14
	# Prompt: "OpenAI sometimes returns JSON wrapped in markdown code fences (```json ... ```), 
	# or with extra text before/after. Sometimes the JSON is malformed. I need a function that 
	# strips code fences, tries to parse the full text, and if that fails, extracts just the 
	# JSON fragment (content between first '{' and last '}'). Can you help me write this 
	# robust JSON parser?"
	# ChatGPT provided the JSON parsing logic with multiple fallback strategies. It first 
	# strips markdown code fences, then attempts to parse the full payload. If that fails, 
	# it extracts the JSON fragment (first '{' to last '}') and tries parsing that. This 
	# handles various OpenAI response formats and ensures JSON can be extracted even from 
	# responses with extra text.
	def _parse_json(self, text: str) -> Dict[str, Any]:
		payload = text.strip()
		if payload.startswith("```"):
			payload = self._strip_fence(payload)

		try:
			return json.loads(payload)
		except json.JSONDecodeError:
			fragment = self._extract_json_fragment(payload)
			if fragment:
				try:
					return json.loads(fragment)
				except json.JSONDecodeError:
					pass
		raise ChatGPTClientError("OpenAI response was not valid JSON.")

	def _normalise_items(self, subtasks: List[Dict[str, Any]]) -> List[BreakdownItem]:
		items: List[BreakdownItem] = []
		for index, row in enumerate(subtasks, start=1):
			title = self._safe_str(row.get("title")) or f"Step {index}"
			description = (
				self._safe_str(row.get("description"))
				or self._safe_str(row.get("details"))
				or ""
			)
			sequence = row.get("sequence") or index
			estimated = row.get("estimated_hours")
			if isinstance(estimated, str):
				try:
					estimated = float(estimated)
				except ValueError:
					estimated = None
			elif isinstance(estimated, (int, float)):
				estimated = float(estimated)
			else:
				estimated = None

			items.append(
				BreakdownItem(
					sequence=int(sequence),
					title=title,
					description=description,
					estimated_hours=estimated,
					planned_start=self._safe_str(row.get("planned_start") or row.get("start")),
					planned_end=self._safe_str(row.get("planned_end") or row.get("end")),
					focus=self._safe_str(row.get("focus") or row.get("tip")),
				)
			)
		return items

	# Reference: ChatGPT (OpenAI) - JSON Fragment Extraction
	# Date: 2025-11-14
	# Prompt: "If a string contains JSON mixed with other text, how can I extract just the 
	# JSON portion? I need to find the first '{' and the last '}' and extract everything 
	# between them. Can you show me this extraction logic?"
	# ChatGPT provided the JSON fragment extraction algorithm that finds the first '{' and 
	# last '}' in a string to extract the JSON content. This is used as a fallback when 
	# OpenAI returns JSON embedded in explanatory text.
	def _extract_json_fragment(self, text: str) -> Optional[str]:
		start = text.find("{")
		end = text.rfind("}")
		if start == -1 or end == -1 or end <= start:
			return None
		return text[start:end + 1]

	def _strip_fence(self, text: str) -> str:
		lines = text.splitlines()
		if lines and lines[0].startswith("```"):
			lines = lines[1:]
		if lines and lines[-1].startswith("```"):
			lines = lines[:-1]
		return "\n".join(lines).strip()

	def _safe_str(self, value: Any) -> Optional[str]:
		if value is None:
			return None
		try:
			return str(value).strip()
		except Exception:
			return None

	def _clean_markdown(self, text: str) -> str:
		if not text:
			return ""
		lines = []
		for line in text.splitlines():
			trimmed = line.strip()
			if not trimmed:
				continue
			# Remove markdown headers and bullets
			while trimmed.startswith("#"):
				trimmed = trimmed[1:].strip()
			if trimmed.startswith(("-", "*", "•")):
				trimmed = trimmed[1:].strip()
			# Remove bold/italic markers
			trimmed = trimmed.replace("**", "").replace("__", "").replace("*", "").replace("_", "")
			lines.append(trimmed)
		return "\n".join(lines).strip()

	def get_study_recommendations(
		self,
		*,
		tasks_summary: str,
		progress_summary: str,
		schedule_summary: Optional[str] = None
	) -> str:
		# Reference: ChatGPT (OpenAI) - Study Recommendations Prompt
		# Date: 2026-01-22
		# Prompt: "I need a study planner prompt that outputs actionable advice in numbered
		# steps without markdown. Can you craft a prompt for that?"
		# ChatGPT provided the prompt structure and output constraints.
		"""Generate AI-based study recommendations for planning and prioritization."""
		system_prompt = (
			"You are an experienced academic coach and study strategist. "
			"Provide personalized, actionable study recommendations based on the student's current workload, progress, and schedule. "
			"Focus on practical advice for task prioritization, time management, and study strategies. "
			"Be encouraging and specific in your recommendations."
		)

		user_prompt_lines = [
			"Analyze the student's current situation and provide personalized study recommendations.",
			"Focus on:",
			"  - Task prioritization (which assignments to tackle first)",
			"  - Time management strategies",
			"  - Study techniques and approaches",
			"  - Ways to improve productivity",
			"",
			"Return your recommendations as clear, well-structured text (not JSON).",
			"Do NOT use markdown headings, hashtags, or bold/italic markers.",
			"Use a numbered list (1., 2., 3., etc.) for easy reading.",
			"Write 6-8 recommendations, each 2-3 sentences long and specific.",
			"",
			"Student's current tasks and workload:",
			tasks_summary,
			"",
			"Progress overview:",
			progress_summary,
		]

		if schedule_summary:
			user_prompt_lines.extend([
				"",
				"Schedule context:",
				schedule_summary
			])

		user_prompt = "\n".join(user_prompt_lines)

		try:
			response = self._client.responses.create(
				model=self._model_name,
				input=[
					{"role": "system", "content": system_prompt},
					{"role": "user", "content": user_prompt},
				],
				temperature=0.6,  # Slightly higher for more varied recommendations
				max_output_tokens=1500,
			)

			text = self._extract_text(response)
			return self._clean_markdown(text)
		except Exception as exc:
			raise ChatGPTClientError(f"Failed to generate study recommendations: {exc}") from exc
