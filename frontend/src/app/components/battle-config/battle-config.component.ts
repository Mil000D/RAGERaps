import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { BattleService } from '../../services/battle.service';
import { BattleCreate } from '../../models/battle.model';
import { BattleConfig } from '../../models/battle-config.model';

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
  loading: boolean = false;
  errorMessage: string = '';
  
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
      style1: this.rapper1Style || 'Freestyle',
      style2: this.rapper2Style || 'Freestyle',
      rapper1_name: this.rapper1Name,
      rapper2_name: this.rapper2Name
    };
    
    // Show loading state
    this.loading = true;
    this.errorMessage = '';
    
    // Use our updated battle service to create the battle with verses
    this.battleService.generateBattleWithVerses(battleCreate)
      .subscribe({
        next: (battle) => {
          this.loading = false;
          if (battle && battle.id) {
            this.router.navigate(['/battle/arena', battle.id]);
          } else {
            console.error("Failed to create battle");
            this.errorMessage = "Failed to create battle. Please try again.";
          }
        },
        error: (err) => {
          this.loading = false;
          console.error("Error creating battle:", err);
          this.errorMessage = "An error occurred while creating the battle. Please try again.";
        }
      });
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
