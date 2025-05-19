import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { environment } from '../../environments/environment';
import { Rapper } from '../models/rapper.model';

@Injectable({
  providedIn: 'root'
})
export class RapperService {
  private apiUrl = `${environment.apiUrl}/rappers`;
  
  // Placeholder data for development
  private mockRappers: Rapper[] = [
    { id: '1', name: 'Kendrick Lamar', wins: 0 },
    { id: '2', name: 'Drake', wins: 0 },
    { id: '3', name: 'Jay-Z', wins: 0 },
    { id: '4', name: 'Nicki Minaj', wins: 0 },
    { id: '5', name: 'Eminem', wins: 0 },
  ];

  constructor(private http: HttpClient) { }

  getRappers(): Observable<Rapper[]> {
    // For now, we'll use the mock data since we don't have a rappers endpoint
    // When the backend has a rappers endpoint, we can use:
    // return this.http.get<Rapper[]>(this.apiUrl)
    //   .pipe(
    //     catchError(this.handleError<Rapper[]>('getRappers', []))
    //   );
    
    return of(this.mockRappers);
  }

  getRapper(id: string): Observable<Rapper | undefined> {
    // For now, use mock data
    // When the backend has a rappers endpoint, we can use:
    // const url = `${this.apiUrl}/${id}`;
    // return this.http.get<Rapper>(url)
    //   .pipe(
    //     catchError(this.handleError<Rapper>(`getRapper id=${id}`))
    //   );
    
    return of(this.mockRappers.find(rapper => rapper.id === id));
  }

  getOrCreateRapper(name: string): Observable<Rapper> {
    // Try to find the rapper by name first
    const existingRapper = this.mockRappers.find(rapper => 
      rapper.name.toLowerCase() === name.toLowerCase()
    );
    
    if (existingRapper) {
      return of(existingRapper);
    }
    
    // If not found, create a new rapper
    const newRapper = { 
      id: `custom-${Date.now()}`,
      name, 
      wins: 0
    };
    
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
