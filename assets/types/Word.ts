export type Word = {
    name: string;
    partOfSpeech:string[]
    definition:{[partOfSpeech: string]: string[]}
    example:{[partOfSpeech: string]: string[]}
    recent: number
  };