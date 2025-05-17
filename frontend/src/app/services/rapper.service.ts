import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { catchError, map } from 'rxjs/operators';

export interface Rapper {
  id?: string;
  name: string;
  image?: string;
  description?: string;
}

@Injectable({
  providedIn: 'root'
})
export class RapperService {
  private apiUrl = '/api/rappers';
  
  // Placeholder data for development
  private mockRappers: Rapper[] = [
    { id: '1', name: 'MC Swift', image: 'assets/rappers/mc-swift.jpg', description: 'Known for lightning-fast rhymes and clever wordplay.' },
    { id: '2', name: 'Lyric Master', image: 'assets/rappers/lyric-master.jpg', description: 'Legendary for complex rhyme schemes and deep messages.' },
    { id: '3', name: 'Beat Professor', image: 'assets/rappers/beat-professor.jpg', description: 'Always in perfect rhythm with the beat.' },
    { id: '4', name: 'Flow Queen', image: 'assets/rappers/flow-queen.jpg', description: 'Smooth delivery that never misses a beat.' },
    { id: '5', name: 'Verbal Assassin', image: 'assets/rappers/verbal-assassin.jpg', description: 'Known for brutal diss tracks and fierce comebacks.' },
  ];

  constructor(private http: HttpClient) { }

  getRappers(): Observable<Rapper[]> {
    // Uncomment to use real API once it's ready
    // return this.http.get<Rapper[]>(this.apiUrl)
    //   .pipe(
    //     catchError(this.handleError<Rapper[]>('getRappers', []))
    //   );
    
    return of(this.mockRappers);
  }

  getRapper(id: string): Observable<Rapper | undefined> {
    // Uncomment to use real API once it's ready
    // const url = `${this.apiUrl}/${id}`;
    // return this.http.get<Rapper>(url)
    //   .pipe(
    //     catchError(this.handleError<Rapper>(`getRapper id=${id}`))
    //   );
    
    return of(this.mockRappers.find(rapper => rapper.id === id));
  }

  createRapper(rapper: Rapper): Observable<Rapper> {
    // Uncomment to use real API once it's ready
    // return this.http.post<Rapper>(this.apiUrl, rapper)
    //   .pipe(
    //     catchError(this.handleError<Rapper>('createRapper'))
    //   );
    
    const newRapper = { ...rapper, id: Date.now().toString() };
    this.mockRappers.push(newRapper);
    return of(newRapper);
  }

  private handleError<T>(operation = 'operation', result?: T) {
    return (error: any): Observable<T> => {
      console.error(`${operation} failed: ${error.message}`);
      // Let the app keep running by returning an empty result
      return of(result as T);
    };
  }
}
