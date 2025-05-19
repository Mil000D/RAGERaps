import { Rapper } from './rapper.model';

export interface BattleConfig {
  rapper1: Rapper;
  rapper2: Rapper;
  rounds: number;
  topic: string;
  style: string;
}

export interface Verse {
  id?: string;
  content: string;
  rapper_name: string;
  created_at?: string;
}

export interface Judgment {
  id?: string;
  winner: string;
  feedback: string;
  created_at?: string;
  is_ai_judgment: boolean;
}

export interface Round {
  id?: string;
  verses: Verse[];
  judgment?: Judgment;
  created_at?: string;
  completed: boolean;
}

export interface Battle {
  id?: string;
  style: string;
  rapper1: Rapper;
  rapper2: Rapper;
  status: 'in_progress' | 'completed';
  winner?: string;
  rounds: Round[];
  created_at?: string;
}

export interface BattleCreate {
  style: string;
  rapper1_name: string;
  rapper2_name: string;
}

export interface JudgmentCreate {
  round_id: string;
  winner: string;
  feedback: string;
}
