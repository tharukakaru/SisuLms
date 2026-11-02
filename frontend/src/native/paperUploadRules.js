export const PAPER_ACCEPT='.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.png,.jpg,.jpeg,.webp'
export const PAPER_MAX_BYTES=10*1024*1024
export function validatePaperUpload(title,file){
  if(!title.trim()||title.length>120)throw Error('Enter a paper title of at most 120 characters.')
  if(!file)throw Error('Choose a document to upload.')
  if(!PAPER_ACCEPT.split(',').includes('.'+file.name.split('.').at(-1).toLowerCase()))throw Error('Choose one of the supported document formats.')
  if(!file.size||file.size>PAPER_MAX_BYTES)throw Error('Choose a nonempty document of at most 10 MB.')
}
