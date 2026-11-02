"""Pure classroom quiz validation and grading; never trusts client scores."""


def normalize(data, complete=False):
    if not isinstance(data, dict):
        raise ValueError('Quiz must be an object')
    def text(value, limit, label):
        if not isinstance(value, str) or len(value) > limit:
            raise ValueError(f'{label} must be text of at most {limit} characters')
        return value.strip()
    title = text(data.get('title', ''), 120, 'Title')
    instructions = text(data.get('instructions', ''), 2000, 'Instructions')
    rows = data.get('questions', [])
    if not isinstance(rows, list) or not 0 <= len(rows) <= 50:
        raise ValueError('Use at most 50 questions')
    if complete and (not title or not rows):
        raise ValueError('Publishing requires a title and 1–50 questions')
    questions = []
    for i, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            raise ValueError(f'Question {i} is invalid')
        prompt = text(row.get('prompt', ''), 3000, f'Question {i}')
        options = row.get('options')
        if not isinstance(options, list) or len(options) != 4:
            raise ValueError(f'Question {i} requires exactly four options')
        options = [text(o, 500, f'Question {i} option') for o in options]
        answer = row.get('answer')
        if answer is not None and (type(answer) is not int or answer not in range(4)):
            raise ValueError(f'Question {i} requires exactly one correct option')
        if complete and (not prompt or not all(options) or answer is None):
            raise ValueError(f'Complete question {i}, all four options and its correct answer')
        questions.append({'prompt': prompt, 'options': options, 'answer': answer})
    return {'title': title, 'instructions': instructions, 'questions': questions}


def public_questions(questions):
    return [{'prompt': q['prompt'], 'options': list(q['options'])} for q in questions]


def grade(questions, answers):
    if not isinstance(answers, list) or len(answers) != len(questions):
        raise ValueError('Answer every question before submitting')
    if any(type(a) is not int or a not in range(4) for a in answers):
        raise ValueError('Choose one option for every question')
    correct = [a == q['answer'] for q, a in zip(questions, answers)]
    return {'score': sum(correct), 'total': len(questions),
            'percentage': round(sum(correct) * 100 / len(questions), 2), 'correctness': correct}
