import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { RapperService, Rapper } from '../../services/rapper.service';
import { BattleService, BattleConfig } from '../../services/battle.service';

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
    rapper1: {} as Rapper,
    rapper2: {} as Rapper,
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
    
    // Create rapper objects from the input fields
    this.config.rapper1 = {
      name: this.rapper1Name,
      id: `custom-${Date.now()}-1` // Generate a unique ID
    };
    
    this.config.rapper2 = {
      name: this.rapper2Name,
      id: `custom-${Date.now()}-2` // Generate a unique ID
    };
    
    // Add rapper styles to the config
    this.config.style = `${this.rapper1Style} vs ${this.rapper2Style}`;
    
    this.battleService.createBattle(this.config)
      .subscribe(() => {
        this.router.navigate(['/battle/arena']);
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
