import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { BattleService, Battle, Verse, Round, BattleResult } from '../../services/battle.service';
import { BattleDisplayComponent } from '../battle-display/battle-display.component';

@Component({
  selector: 'app-battle-arena',
  standalone: true,
  imports: [CommonModule, BattleDisplayComponent],
  templateUrl: './battle-arena.component.html',
  styleUrl: './battle-arena.component.css'
})
export class BattleArenaComponent implements OnInit {
  battle: Battle | null = null;
  currentRound = 0;
  loading = false;
  generating = false;
  battleComplete = false;
  battleResult: BattleResult | null = null;
  
  constructor(
    private battleService: BattleService,
    private router: Router
  ) {}
  
  ngOnInit(): void {
    this.battle = this.battleService.getCurrentBattle();
    
    if (!this.battle) {
      // If no battle is found, redirect back to config
      this.router.navigate(['/battle']);
      return;
    }
    
    this.startNextRound();
  }
  
  startNextRound(): void {
    if (!this.battle || this.battleComplete) {
      return;
    }
    
    this.currentRound++;
    if (this.currentRound > this.battle.config.rounds) {
      this.completeBattle();
      return;
    }
    
    this.generating = true;
    
    // Generate first verse
    if (this.battle && this.battle.config && this.battle.config.rapper1) {
      this.battleService.generateVerse(this.battle.config.rapper1, this.currentRound)
        .subscribe(verse1 => {
          // Generate second verse
          if (this.battle && this.battle.config && this.battle.config.rapper2) {
            this.battleService.generateVerse(this.battle.config.rapper2, this.currentRound, [verse1])
              .subscribe(verse2 => {
                // Judge the round
                this.battleService.judgeRound(verse1, verse2)
                  .subscribe(round => {
                    this.generating = false;
                  });
              });
          }
        });
    }
  }
  
  completeBattle(): void {
    if (!this.battle) {
      return;
    }
    
    this.loading = true;
    this.battleService.completeBattle()
      .subscribe(result => {
        this.battleResult = result;
        this.battleComplete = true;
        this.loading = false;
      });
  }
  
  configureNewBattle(): void {
    this.router.navigate(['/battle']);
  }
  
  getInitial(name: string): string {
    return name ? name.charAt(0).toUpperCase() : 'R';
  }
}
