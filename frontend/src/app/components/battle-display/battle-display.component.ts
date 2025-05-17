import { Component, Input, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Round, Verse } from '../../services/battle.service';
import { Rapper } from '../../services/rapper.service';

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
    // Initial animation delay
  }
  
  startJudging(): void {
    this.isJudging = true;
    setTimeout(() => {
      this.judgeResult = true;
    }, 3000);
  }
  
  getWinnerClass(rapper: Rapper): string {
    if (!this.judgeResult) return '';
    return this.round.winner?.id === rapper.id ? 'winner' : 'loser';
  }
  
  getInitial(name: string): string {
    return name ? name.charAt(0).toUpperCase() : 'R';
  }
}
