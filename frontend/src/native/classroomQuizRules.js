export const emptyQuestion = () => ({prompt:'', options:['','','',''], answer:null})
export function quizErrors(quiz) {
  const errors={questions:[]}
  if(!quiz.title?.trim())errors.title='Enter a quiz title.'
  else if(quiz.title.length>120)errors.title='Use at most 120 characters.'
  if(!Array.isArray(quiz.questions)||quiz.questions.length<1||quiz.questions.length>50)errors.count='Use 1–50 questions.'
  for(const q of quiz.questions||[]){
    const e={}
    if(!q.prompt?.trim())e.prompt='Enter the question text.'
    else if(q.prompt.length>3000)e.prompt='Use at most 3,000 characters.'
    if(q.options?.length!==4||q.options.some(o=>typeof o!=='string'||!o.trim()||o.length>500))e.options='Enter four options, each with 1–500 characters.'
    if(!Number.isInteger(q.answer)||q.answer<0||q.answer>3)e.answer='Choose exactly one correct option.'
    errors.questions.push(e)
  }
  return errors
}
export const hasQuizErrors = errors => !!(errors.title||errors.count||errors.questions.some(e=>Object.keys(e).length))
export const completeAnswers = (questions, answers) => questions.length>0&&answers.length===questions.length&&answers.every(a=>Number.isInteger(a)&&a>=0&&a<4)
