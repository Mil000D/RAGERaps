import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { RapperService } from '../../services/rapper.service';
import { BattleService } from '../../services/battle.service';
import { BattleCreate } from '../../models/battle.model';
import { BattleConfig } from '../../models/battle-config.model';
import { Rapper } from '../../models/rapper.model';

@Component({
  selector: 'app-battle-config',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './battle-config.component.html',
  styleUrl: './battle-config.component.css'
})
export class BattleConfigComponent implements OnInit {
  rapper1Name: string = '';
  rapper1Style: string = '';
  rapper2Name: string = '';
  rapper2Style: string = '';
  
  config: BattleConfig = {
    rapper1: { name: '' },
    rapper2: { name: '' },
    rounds: 3,
    topic: '',
    style: ''
  };
  
  topics: string[] = [
    'Money & Success',
    'Street Life',
    'Competition',
    'Old School vs New School',
    'Personal Growth',
    'Love & Relationships',
    'Social Issues',
    'Party Life',
    'Legacy & Fame'
  ];
  
  constructor(
    private rapperService: RapperService,
    private battleService: BattleService,
    private router: Router
  ) {}
  
  ngOnInit(): void {
    // No need to load rappers anymore
  }
  
  startBattle(): void {
    if (!this.isValidConfig()) {
      return;
    }
    
    // Create a BattleCreate object for the API
    const battleCreate: BattleCreate = {
      style: this.determineStyle(),
      rapper1_name: this.rapper1Name,
      rapper2_name: this.rapper2Name
    };
    
    // Use our updated battle service to create the battle with verses
    this.battleService.generateBattleWithVerses(battleCreate)
      .subscribe(battle => {
        if (battle) {
          this.router.navigate(['/battle/arena', battle.id]);
        } else {
          console.error("Failed to create battle");
        }
      });
  }
  
  // Helper method to determine the combined style
  private determineStyle(): string {
    if (this.rapper1Style && this.rapper2Style) {
      return `${this.rapper1Style} vs ${this.rapper2Style}`;
    } else if (this.rapper1Style) {
      return this.rapper1Style;
    } else if (this.rapper2Style) {
      return this.rapper2Style;
    } else {
      return 'Freestyle'; // Default style
    }
  }
  
  isValidConfig(): boolean {
    return (
      !!this.rapper1Name && 
      !!this.rapper2Name && 
      this.rapper1Name !== this.rapper2Name &&
      this.config.rounds > 0 &&
      this.config.rounds <= 5
    );
  }
}
