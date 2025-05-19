import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { Battle } from '../../models/battle.model';
import { BattleService } from '../../services/battle.service';

@Component({
  selector: 'app-battle-list',
  standalone: true,
  imports: [CommonModule],
  template: `
    <section class="battles-container">
      <h1>RAGERaps Battles</h1>
      
      <div *ngIf="loading" class="loading">Loading battles...</div>
      <div *ngIf="error" class="error">{{ error }}</div>
      
      <div *ngIf="!loading && battles.length === 0" class="no-battles">
        No rap battles found. Create a new battle to get started!
      </div>
      
      <div class="battles-list" *ngIf="!loading && battles.length > 0">
        <div *ngFor="let battle of battles" class="battle-card" 
             (click)="viewBattle(battle.id!)">
          <div class="battle-header">
            <h3>{{ battle.rapper1.name }} vs {{ battle.rapper2.name }}</h3>
            <span class="battle-style">{{ battle.style }} Style</span>
          </div>
          
          <div class="battle-status">
            <span [class.completed]="battle.status === 'completed'">
              {{ battle.status === 'completed' ? 'Completed' : 'In Progress' }}
            </span>
            <span *ngIf="battle.winner" class="winner">
              Winner: {{ battle.winner }}
            </span>
          </div>
          
          <div class="battle-score">
            {{ battle.rapper1.wins }} - {{ battle.rapper2.wins }}
          </div>
          
          <div class="battle-date">
            {{ battle.created_at | date:'medium' }}
          </div>
        </div>
      </div>
      
      <button class="new-battle-btn" (click)="createNewBattle()">
        Create New Battle
      </button>
    </section>
  `,
  styles: [`
    .battles-container {
      max-width: 800px;
      margin: 0 auto;
      padding: 20px;
    }
    .battle-card {
      background-color: #252525;
      border-radius: 8px;
      padding: 16px;
      margin-bottom: 16px;
      cursor: pointer;
      transition: transform 0.2s;
    }
    .battle-card:hover {
      transform: translateY(-3px);
      box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .battle-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
    }
    .battle-style {
      background-color: #333;
      padding: 4px 8px;
      border-radius: 4px;
    }
    .battle-status {
      display: flex;
      justify-content: space-between;
      margin-bottom: 8px;
    }
    .completed {
      color: #4caf50;
    }
    .winner {
      font-weight: bold;
    }
    .battle-score {
      font-size: 1.2rem;
      font-weight: bold;
      text-align: center;
    }
    .battle-date {
      font-size: 0.8rem;
      color: #888;
      text-align: right;
      margin-top: 8px;
    }
    .new-battle-btn {
      background-color: #f44336;
      color: white;
      border: none;
      padding: 12px 24px;
      border-radius: 4px;
      font-size: 1rem;
      cursor: pointer;
      margin-top: 20px;
      transition: background-color 0.3s;
    }
    .new-battle-btn:hover {
      background-color: #d32f2f;
    }
    .loading, .error, .no-battles {
      text-align: center;
      padding: 20px;
      background-color: #252525;
      border-radius: 8px;
      margin-bottom: 20px;
    }
    .error {
      color: #f44336;
    }
  `]
})
export class BattleListComponent implements OnInit {
  battles: Battle[] = [];
  loading = false;
  error: string | null = null;
  
  constructor(
    private battleService: BattleService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loadBattles();
  }
  
  loadBattles(): void {
    this.loading = true;
    this.battleService.getBattles().subscribe({
      next: (battles) => {
        this.battles = battles;
        this.loading = false;
      },
      error: (err) => {
        console.error('Error loading battles', err);
        this.error = 'Failed to load battles. Please try again later.';
        this.loading = false;
      }
    });
  }
  
  viewBattle(id: string): void {
    this.router.navigate(['/battle/arena', id]);
  }
  
  createNewBattle(): void {
    this.router.navigate(['/battle']);
  }
}
