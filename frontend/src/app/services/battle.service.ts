import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, catchError, of, tap } from 'rxjs';
import { environment } from '../../environments/environment';
import { Battle, BattleCreate, JudgmentCreate } from '../models/battle.model';

@Injectable({
  providedIn: 'root'
})
export class BattleService {
  private apiUrl = `${environment.apiUrl}/api/battles`;

  constructor(private http: HttpClient) { }

  /**
   * Get all battles
   */
  getBattles(): Observable<Battle[]> {
    console.log('Fetching all battles from API');
    return this.http.get<Battle[]>(this.apiUrl).pipe(
      tap(battles => console.log('Fetched battles', battles)),
      catchError(this.handleError<Battle[]>('getBattles', []))
    );
  }

  /**
   * Get a single battle by ID
   */
  getBattle(id: string): Observable<Battle> {
    console.log(`Fetching battle with ID ${id} from API`);
    return this.http.get<Battle>(`${this.apiUrl}/${id}`).pipe(
      tap(battle => console.log('Fetched battle', battle)),
      catchError(this.handleError<Battle>(`getBattle id=${id}`))
    );
  }

  /**
   * Generate a new battle with verses for both rappers
   */
  generateBattleWithVerses(battleData: BattleCreate): Observable<Battle> {
    console.log('Creating new battle with verses', battleData);
    const payload = {
      style1: battleData.style1 || 'Freestyle',
      style2: battleData.style2 || 'Freestyle',
      rapper1_name: battleData.rapper1_name,
      rapper2_name: battleData.rapper2_name
    };

    return this.http.post<Battle>(`${this.apiUrl}/with-verses`, payload).pipe(
      tap(battle => console.log('Created new battle', battle)),
      catchError(this.handleError<Battle>('generateBattleWithVerses'))
    );
  }

  /**
   * Judge a round using AI
   */
  judgeRoundWithAI(battleId: string, roundId: string): Observable<Battle> {
    console.log(`AI judging round ${roundId} in battle ${battleId}`);
    return this.http.post<Battle>(`${this.apiUrl}/${battleId}/rounds/${roundId}/judge`, {}).pipe(
      tap(battle => console.log('AI judged round', battle)),
      catchError(this.handleError<Battle>('judgeRoundWithAI'))
    );
  }

  /**
   * Judge a round manually by user
   */
  judgeRoundByUser(battleId: string, roundId: string, judgment: JudgmentCreate): Observable<Battle> {
    console.log(`User judging round ${roundId} in battle ${battleId}`, judgment);
    return this.http.post<Battle>(`${this.apiUrl}/${battleId}/rounds/${roundId}/user-judge`, judgment).pipe(
      tap(battle => console.log('User judged round', battle)),
      catchError(this.handleError<Battle>('judgeRoundByUser'))
    );
  }

  /**
   * Handle HTTP operation that failed.
   * Let the app continue.
   * @param operation - name of the operation that failed
   * @param result - optional value to return as the observable result
   */
  private handleError<T>(operation = 'operation', result?: T) {
    return (error: any): Observable<T> => {
      console.error(`${operation} failed:`, error);
      console.error(`${operation} error message:`, error.message);

      // Let the app keep running by returning an empty result
      return of(result as T);
    };
  }
}

