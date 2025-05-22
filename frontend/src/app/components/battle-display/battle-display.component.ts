import { Component, Input, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Round, Verse } from '../../models/battle.model';

@Component({
  selector: 'app-battle-display',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './battle-display.component.html',
  styleUrl: './battle-display.component.css'
})
export class BattleDisplayComponent implements OnInit {
  @Input() round!: Round;
  @Input() roundNumber!: number;
  @Input() totalRounds!: number;
  
  isJudging = false;
  judgeResult = false;
  
  ngOnInit(): void {
    
  }
  
  startJudging(): void {
    this.isJudging = true;
    setTimeout(() => {
      this.judgeResult = true;
    }, 3000);
  }
  
  getWinnerClass(rapperName: string): string {
    if (!this.judgeResult) return '';
    return this.round.winner === rapperName ? 'winner' : 'loser';
  }
  
  getInitial(name: string): string {
    return name ? name.charAt(0).toUpperCase() : 'R';
  }
}
