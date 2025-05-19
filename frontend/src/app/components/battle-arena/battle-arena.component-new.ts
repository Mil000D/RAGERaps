import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, ActivatedRoute } from '@angular/router';
import { FormsModule, FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { BattleService } from '../../services/battle.service';
import { Battle, Round, JudgmentCreate } from '../../models/battle.model';

@Component({
  selector: 'app-battle-arena',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule],
  template: `
    <section class="battle-arena">
      <div class="container arena-container">
        <header class="arena-header">
          <h2 class="arena-title">RAGE<span class="title-highlight">Raps</span> Battle Arena</h2>
        </header>
        
        <div *ngIf="loading" class="loading-state">
          <div class="spinner"></div>
          <p>Loading battle...</p>
        </div>
        
        <div *ngIf="error" class="error-state">
          <p>{{ error }}</p>
          <button class="back-btn" (click)="navigateBack()">Back to battles</button>
        </div>
        
        <div *ngIf="battle && !loading && !error" class="battle-content">
          <!-- Battle Header -->
          <div class="versus-display">
            <div class="rapper-info" [class.winner]="battle.winner === battle.rapper1.name">
              <div class="rapper-initial">{{ getInitial(battle.rapper1.name) }}</div>
              <h3 class="rapper-name">{{ battle.rapper1.name }}</h3>
              <div class="rapper-score">{{ battle.rapper1.wins }}</div>
            </div>
            
            <div class="versus-circle">VS</div>
            
            <div class="rapper-info" [class.winner]="battle.winner === battle.rapper2.name">
              <div class="rapper-initial">{{ getInitial(battle.rapper2.name) }}</div>
              <h3 class="rapper-name">{{ battle.rapper2.name }}</h3>
              <div class="rapper-score">{{ battle.rapper2.wins }}</div>
            </div>
          </div>
          
          <div class="battle-style">
            <span class="style-label">Style:</span> {{ battle.style }}
          </div>
          
          <!-- Battle Status -->
          <div class="battle-status" [class.completed]="battle.status === 'completed'">
            {{ battle.status === 'completed' ? 'Battle Complete' : 'Battle In Progress' }}
            <span *ngIf="battle.winner" class="winner-text">
              Winner: {{ battle.winner }}
            </span>
          </div>
          
          <!-- Rounds -->
          <div class="rounds-container">
            <div *ngFor="let round of battle.rounds; let i = index" class="round">
              <h3 class="round-header">Round {{ i + 1 }}</h3>
              
              <!-- Verses -->
              <div class="verses">
                <div *ngFor="let verse of round.verses" class="verse">
                  <h4 class="verse-rapper">{{ verse.rapper_name }}</h4>
                  <pre class="verse-content">{{ verse.content }}</pre>
                </div>
              </div>
              
              <!-- Judgment -->
              <div *ngIf="round.judgment" class="judgment">
                <h4>Judgment</h4>
                <div class="judgment-winner">
                  Winner: <strong>{{ round.judgment.winner }}</strong>
                </div>
                <div class="judgment-feedback">
                  {{ round.judgment.feedback }}
                </div>
                <div class="judgment-type">
                  <small>{{ round.judgment.is_ai_judgment ? 'AI Judgment' : 'User Judgment' }}</small>
                </div>
              </div>
              
              <!-- Judge Controls -->
              <div *ngIf="!round.judgment && round.verses.length === 2" class="judge-controls">
                <div class="judge-options">
                  <button class="ai-judge-btn" (click)="judgeRoundWithAI(round)" [disabled]="judging">
                    {{ judging ? 'AI is judging...' : 'Let AI Judge' }}
                  </button>
                  
                  <div class="manual-judgment">
                    <h4>Judge yourself</h4>
                    <form [formGroup]="judgmentForm" (ngSubmit)="submitUserJudgment(round)">
                      <div class="form-group">
                        <label>Select Winner:</label>
                        <div class="radio-options">
                          <label>
                            <input type="radio" formControlName="winner" [value]="battle.rapper1.name">
                            {{ battle.rapper1.name }}
                          </label>
                          <label>
                            <input type="radio" formControlName="winner" [value]="battle.rapper2.name">
                            {{ battle.rapper2.name }}
                          </label>
                        </div>
                      </div>
                      
                      <div class="form-group">
                        <label for="feedback">Your Feedback:</label>
                        <textarea id="feedback" formControlName="feedback" 
                          placeholder="Why did this rapper win?"></textarea>
                      </div>
                      
                      <button type="submit" class="submit-btn" 
                        [disabled]="judgmentForm.invalid || judging">
                        Submit Your Judgment
                      </button>
                    </form>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div class="battle-actions">
            <button class="back-btn" (click)="navigateBack()">Back to battles</button>
            <button *ngIf="battle.status === 'completed'" class="new-battle-btn" (click)="startNewBattle()">
              New Battle
            </button>
          </div>
        </div>
      </div>
    </section>
  `,
  styles: [`
    .battle-arena {
      padding: 20px;
      max-width: 900px;
      margin: 0 auto;
    }
    
    .arena-header {
      text-align: center;
      margin-bottom: 30px;
    }
    
    .arena-title {
      font-size: 2.4rem;
      margin: 0;
    }
    
    .title-highlight {
      color: #f44336;
    }
    
    .versus-display {
      display: flex;
      justify-content: space-around;
      align-items: center;
      margin-bottom: 20px;
    }
    
    .rapper-info {
      text-align: center;
      flex: 1;
    }
    
    .rapper-info.winner {
      position: relative;
    }
    
    .rapper-info.winner::before {
      content: '👑';
      position: absolute;
      top: -20px;
      left: 50%;
      transform: translateX(-50%);
    }
    
    .rapper-initial {
      width: 60px;
      height: 60px;
      border-radius: 50%;
      background-color: #333;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.8rem;
      font-weight: bold;
      margin: 0 auto 10px;
    }
    
    .rapper-name {
      margin: 0;
      font-size: 1.2rem;
    }
    
    .rapper-score {
      font-size: 2rem;
      font-weight: bold;
      margin-top: 5px;
    }
    
    .versus-circle {
      width: 60px;
      height: 60px;
      border-radius: 50%;
      background-color: #f44336;
      color: white;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: bold;
      font-size: 1.2rem;
    }
    
    .battle-style {
      text-align: center;
      background-color: #333;
      padding: 8px;
      border-radius: 4px;
      margin-bottom: 20px;
    }
    
    .style-label {
      font-weight: bold;
      color: #f44336;
    }
    
    .battle-status {
      text-align: center;
      padding: 10px;
      background-color: #303030;
      border-radius: 4px;
      margin-bottom: 30px;
      font-weight: bold;
    }
    
    .battle-status.completed {
      color: #4caf50;
    }
    
    .winner-text {
      display: block;
      margin-top: 5px;
      color: #f44336;
    }
    
    .rounds-container {
      margin-bottom: 30px;
    }
    
    .round {
      background-color: #252525;
      border-radius: 8px;
      padding: 20px;
      margin-bottom: 20px;
    }
    
    .round-header {
      margin-top: 0;
      border-bottom: 1px solid #444;
      padding-bottom: 10px;
      margin-bottom: 15px;
    }
    
    .verses {
      display: flex;
      flex-direction: column;
      gap: 15px;
      margin-bottom: 20px;
    }
    
    .verse {
      background-color: #303030;
      border-radius: 6px;
      padding: 15px;
    }
    
    .verse-rapper {
      margin-top: 0;
      margin-bottom: 10px;
      color: #f44336;
    }
    
    .verse-content {
      margin: 0;
      white-space: pre-wrap;
      font-family: inherit;
      line-height: 1.5;
    }
    
    .judgment {
      background-color: #333;
      border-radius: 6px;
      padding: 15px;
      margin-bottom: 20px;
    }
    
    .judgment h4 {
      margin-top: 0;
      color: #4caf50;
    }
    
    .judgment-winner {
      margin-bottom: 10px;
    }
    
    .judgment-feedback {
      line-height: 1.5;
    }
    
    .judgment-type {
      margin-top: 10px;
      font-style: italic;
      color: #888;
    }
    
    .judge-controls {
      background-color: #333;
      border-radius: 6px;
      padding: 15px;
    }
    
    .ai-judge-btn {
      width: 100%;
      padding: 12px;
      background-color: #2196f3;
      border: none;
      border-radius: 4px;
      color: white;
      font-size: 1rem;
      cursor: pointer;
      margin-bottom: 20px;
    }
    
    .ai-judge-btn:hover {
      background-color: #1976d2;
    }
    
    .ai-judge-btn:disabled {
      background-color: #555;
      cursor: not-allowed;
    }
    
    .manual-judgment h4 {
      margin-top: 0;
      text-align: center;
      position: relative;
    }
    
    .manual-judgment h4::before,
    .manual-judgment h4::after {
      content: '';
      position: absolute;
      top: 50%;
      width: 30%;
      height: 1px;
      background-color: #555;
    }
    
    .manual-judgment h4::before {
      left: 0;
    }
    
    .manual-judgment h4::after {
      right: 0;
    }
    
    .form-group {
      margin-bottom: 15px;
    }
    
    .radio-options {
      display: flex;
      justify-content: space-around;
      margin-top: 10px;
    }
    
    .radio-options label {
      display: flex;
      align-items: center;
      gap: 5px;
      cursor: pointer;
    }
    
    textarea {
      width: 100%;
      min-height: 80px;
      background-color: #252525;
      border: 1px solid #555;
      border-radius: 4px;
      padding: 10px;
      color: white;
      font-family: inherit;
    }
    
    .submit-btn {
      width: 100%;
      padding: 12px;
      background-color: #4caf50;
      border: none;
      border-radius: 4px;
      color: white;
      font-size: 1rem;
      cursor: pointer;
    }
    
    .submit-btn:hover {
      background-color: #388e3c;
    }
    
    .submit-btn:disabled {
      background-color: #555;
      cursor: not-allowed;
    }
    
    .battle-actions {
      display: flex;
      justify-content: center;
      gap: 20px;
    }
    
    .back-btn, .new-battle-btn {
      padding: 12px 24px;
      border: none;
      border-radius: 4px;
      font-size: 1rem;
      cursor: pointer;
    }
    
    .back-btn {
      background-color: #757575;
      color: white;
    }
    
    .back-btn:hover {
      background-color: #616161;
    }
    
    .new-battle-btn {
      background-color: #f44336;
      color: white;
    }
    
    .new-battle-btn:hover {
      background-color: #d32f2f;
    }
    
    .loading-state, .error-state {
      text-align: center;
      padding: 40px;
      background-color: #252525;
      border-radius: 8px;
    }
    
    .loading-state .spinner {
      width: 40px;
      height: 40px;
      border: 4px solid rgba(255, 255, 255, 0.2);
      border-top-color: #f44336;
      border-radius: 50%;
      margin: 0 auto 20px;
      animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
      to {
        transform: rotate(360deg);
      }
    }
    
    .error-state {
      color: #f44336;
    }
  `]
})
export class BattleArenaComponent implements OnInit {
  battle: Battle | null = null;
  battleId: string | null = null;
  loading = false;
  error: string | null = null;
  judging = false;
  judgmentForm: FormGroup;
  
  constructor(
    private battleService: BattleService,
    private router: Router,
    private route: ActivatedRoute,
    private fb: FormBuilder
  ) {
    this.judgmentForm = this.fb.group({
      winner: ['', Validators.required],
      feedback: ['', Validators.required]
    });
  }
  
  ngOnInit(): void {
    // Get battle ID from route params
    this.route.params.subscribe(params => {
      if (params['id']) {
        this.battleId = params['id'];
        this.loadBattle(this.battleId);
      } else {
        this.router.navigate(['/battle']);
      }
    });
  }
  
  loadBattle(id: string): void {
    this.loading = true;
    this.error = null;
    
    this.battleService.getBattle(id).subscribe({
      next: (battle) => {
        this.battle = battle;
        this.loading = false;
      },
      error: (err) => {
        console.error('Error loading battle', err);
        this.error = 'Failed to load battle. Please try again.';
        this.loading = false;
      }
    });
  }
  
  judgeRoundWithAI(round: Round): void {
    if (!this.battleId || !round.id) {
      return;
    }
    
    this.judging = true;
    this.battleService.judgeRoundWithAI(this.battleId, round.id).subscribe({
      next: (battle) => {
        if (battle) {
          this.battle = battle;
        }
        this.judging = false;
      },
      error: (err) => {
        console.error('Error judging round with AI', err);
        this.error = 'Failed to get AI judgment. Please try again or judge manually.';
        this.judging = false;
      }
    });
  }
  
  submitUserJudgment(round: Round): void {
    if (!this.battleId || !round.id || this.judgmentForm.invalid) {
      return;
    }
    
    const judgment: JudgmentCreate = {
      round_id: round.id,
      winner: this.judgmentForm.value.winner,
      feedback: this.judgmentForm.value.feedback
    };
    
    this.judging = true;
    this.battleService.judgeRoundByUser(this.battleId, round.id, judgment).subscribe({
      next: (battle) => {
        if (battle) {
          this.battle = battle;
          this.judgmentForm.reset();
        }
        this.judging = false;
      },
      error: (err) => {
        console.error('Error judging round', err);
        this.error = 'Failed to submit your judgment. Please try again.';
        this.judging = false;
      }
    });
  }
  
  navigateBack(): void {
    this.router.navigate(['/']);
  }
  
  startNewBattle(): void {
    this.router.navigate(['/battle']);
  }
  
  getInitial(name: string): string {
    return name ? name.charAt(0).toUpperCase() : 'R';
  }
}
