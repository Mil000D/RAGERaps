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
  round_id?: string;
  content: string;
  rapper_name: string;
  created_at?: string;
  updated_at?: string;
  sources?: any[];
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
  battle_id?: string;
  rapper1_verse?: Verse;
  rapper2_verse?: Verse;
  user_judgment?: Judgment | null;
  judge_feedback?: string | null;
  winner?: string | null;
  round_number: number;
  status: 'completed' | 'in_progress';
  created_at?: string;
  updated_at?: string;
}

export interface Battle {
  id?: string;
  style1: string;
  style2: string;
  rapper1_name: string;
  rapper2_name: string;
  status: 'in_progress' | 'completed';
  winner?: string | null;
  rounds: Round[];
  created_at?: string;
  updated_at?: string;
  current_round?: number;
  rapper1_wins?: number;
  rapper2_wins?: number;
}

export interface BattleCreate {
  style1: string;
  style2: string;
  rapper1_name: string;
  rapper2_name: string;
}

export interface JudgmentCreate {
  round_id: string;
  winner: string;
  feedback: string;
}
