import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { Rapper } from './rapper.service';

export interface BattleConfig {
  rapper1: Rapper;
  rapper2: Rapper;
  rounds: number;
  topic?: string;
  style?: string;
}

export interface Verse {
  text: string;
  rapper: Rapper;
  round: number;
}

export interface Round {
  number: number;
  verse1: Verse;
  verse2: Verse;
  winner?: Rapper;
}

export interface BattleResult {
  winner: Rapper;
  rounds: Round[];
  scores: {
    rapper1Score: number;
    rapper2Score: number;
  };
}

export interface Battle {
  id?: string;
  config: BattleConfig;
  rounds: Round[];
  completed: boolean;
  result?: BattleResult;
  createdAt: Date;
}

@Injectable({
  providedIn: 'root'
})
export class BattleService {
  private apiUrl = '/api/battles';
  private currentBattle: Battle | null = null;

  constructor(private http: HttpClient) { }

  createBattle(config: BattleConfig): Observable<Battle> {
    // Uncomment to use real API once it's ready
    // return this.http.post<Battle>(this.apiUrl, config)
    //   .pipe(
    //     catchError(this.handleError<Battle>('createBattle'))
    //   );
    
    // Mock battle creation
    const battle: Battle = {
      id: Date.now().toString(),
      config: config,
      rounds: [],
      completed: false,
      createdAt: new Date()
    };
    this.currentBattle = battle;
    return of(battle);
  }

  getCurrentBattle(): Battle | null {
    return this.currentBattle;
  }

  generateVerse(rapper: Rapper, roundNumber: number, previousVerses?: Verse[]): Observable<Verse> {
    // Uncomment to use real API once it's ready
    // const url = `${this.apiUrl}/verse`;
    // return this.http.post<Verse>(url, { rapper, roundNumber, previousVerses })
    //   .pipe(
    //     catchError(this.handleError<Verse>('generateVerse'))
    //   );
    
    // Mock verse generation
    const mockVerses = [
      "I step to the mic with precision and grace,\nDropping rhymes so hot they're all over the place.\nMy flow is smooth, my beats are tight,\nI'll leave you speechless all through the night.",
      "You think you're good? You ain't seen nothing yet,\nMy lyrics hit harder than your biggest regret.\nI'm the king of this battle, the best of the best,\nAfter I'm done with you, you'll need a long rest.",
      "Your rhymes are weak, your flow is bland,\nTime to step aside and let the master take command.\nI spit fire that burns up the track,\nOnce I start flowing, there's no turning back."
    ];
    
    const verse: Verse = {
      text: mockVerses[Math.floor(Math.random() * mockVerses.length)],
      rapper: rapper,
      round: roundNumber
    };
    
    return of(verse);
  }

  judgeRound(verse1: Verse, verse2: Verse): Observable<Round> {
    // Uncomment to use real API once it's ready
    // const url = `${this.apiUrl}/judge`;
    // return this.http.post<Round>(url, { verse1, verse2 })
    //   .pipe(
    //     catchError(this.handleError<Round>('judgeRound'))
    //   );
    
    // Mock judging
    const round: Round = {
      number: verse1.round,
      verse1: verse1,
      verse2: verse2,
      winner: Math.random() > 0.5 ? verse1.rapper : verse2.rapper
    };
    
    if (this.currentBattle) {
      this.currentBattle.rounds.push(round);
    }
    
    return of(round);
  }

  completeBattle(): Observable<BattleResult> {
    if (!this.currentBattle) {
      throw new Error('No active battle to complete');
    }
    
    // Uncomment to use real API once it's ready
    // const url = `${this.apiUrl}/${this.currentBattle.id}/complete`;
    // return this.http.post<BattleResult>(url, {})
    //   .pipe(
    //     catchError(this.handleError<BattleResult>('completeBattle'))
    //   );
    
    // Mock battle completion
    let rapper1Score = 0;
    let rapper2Score = 0;
    
    this.currentBattle.rounds.forEach(round => {
      if (round.winner?.id === this.currentBattle?.config.rapper1.id) {
        rapper1Score++;
      } else if (round.winner?.id === this.currentBattle?.config.rapper2.id) {
        rapper2Score++;
      }
    });
    
    const result: BattleResult = {
      winner: rapper1Score > rapper2Score 
        ? this.currentBattle.config.rapper1 
        : this.currentBattle.config.rapper2,
      rounds: this.currentBattle.rounds,
      scores: {
        rapper1Score,
        rapper2Score
      }
    };
    
    this.currentBattle.completed = true;
    this.currentBattle.result = result;
    
    return of(result);
  }

  private handleError<T>(operation = 'operation', result?: T) {
    return (error: any): Observable<T> => {
      console.error(`${operation} failed: ${error.message}`);
      return of(result as T);
    };
  }
}
