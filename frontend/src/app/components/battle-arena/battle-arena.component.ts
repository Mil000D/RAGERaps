import {Component, OnInit} from '@angular/core';
import {CommonModule} from '@angular/common';
import {ActivatedRoute, Router} from '@angular/router';
import {FormBuilder, FormGroup, ReactiveFormsModule, Validators} from '@angular/forms';
import {BattleService} from '../../services/battle.service';
import {Battle, JudgmentCreate} from '../../models/battle.model';

@Component({
  selector: 'app-battle-arena',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './battle-arena.component.html',
  styleUrl: './battle-arena.component.css'
})
export class BattleArenaComponent implements OnInit {
  battle: Battle | null = null;
  battleId: string | null = null;
  loading = false;
  error: string | null = null;
  judgmentForm: FormGroup;
  rapper1Wins: number = 0;
  rapper2Wins: number = 0;
  collapsedAnalysis: {[roundId: string]: {rapper1: boolean, rapper2: boolean, comparison: boolean}} = {};

  constructor(
    private battleService: BattleService,
    private router: Router,
    private route: ActivatedRoute,
    private fb: FormBuilder
  ) {
    this.judgmentForm = this.fb.group({
      winner: ['', Validators.required]
    });
  }

  ngOnInit(): void {

    this.route.params.subscribe(params => {
      if (params['id']) {
        this.battleId = params['id'];
        this.loadBattle(params['id']);
      } else {
        this.router.navigate(['/battle']);
      }
    });
  }

  loadBattle(id: string): void {
    this.loading = true;
    this.battleService.getBattle(id).subscribe({
      next: (battle) => {
        this.battle = battle;
        this.loading = false;

        this.rapper1Wins = battle.rapper1_wins || 0;
        this.rapper2Wins = battle.rapper2_wins || 0;
      },
      error: (err) => {
        console.error('Error loading battle', err);
        this.error = 'Failed to load battle. Please try again.';
        this.loading = false;
      }
    });
  }

  judgeRoundWithAI(battleId: string, roundId: string): void {
    if (!this.battle) return;

    this.loading = true;
    this.battleService.judgeRoundWithAI(battleId, roundId).subscribe({
      next: (updatedBattle) => {
        this.battle = updatedBattle;
        this.loading = false;

        this.rapper1Wins = updatedBattle.rapper1_wins || 0;
        this.rapper2Wins = updatedBattle.rapper2_wins || 0;
      },
      error: (err) => {
        console.error('Error judging round with AI', err);
        this.error = 'Failed to judge round with AI. Please try again.';
        this.loading = false;
      }
    });
  }

  judgeRoundByUser(battleId: string, roundId: string): void {
    if (!this.battle || this.judgmentForm.invalid) return;

    const judgment: JudgmentCreate = {
      round_id: roundId,
      winner: this.judgmentForm.value.winner,
      feedback: "User judgment selected " + this.judgmentForm.value.winner + " as the winner."
    };

    this.loading = true;
    this.battleService.judgeRoundByUser(battleId, roundId, judgment).subscribe({
      next: (updatedBattle) => {
        this.battle = updatedBattle;
        this.loading = false;

        const currentRound = updatedBattle.rounds.find(r => r.id === roundId);
        console.log('Updated round after user judgment:', currentRound);
        console.log('User judgment:', currentRound?.user_judgment);

        this.rapper1Wins = updatedBattle.rapper1_wins || 0;
        this.rapper2Wins = updatedBattle.rapper2_wins || 0;
        this.judgmentForm.reset();
      },
      error: (err) => {
        console.error('Error submitting user judgment', err);
        this.error = 'Failed to submit judgment. Please try again.';
        this.loading = false;
      }
    });
  }

  backToList(): void {
    this.router.navigate(['/battle']);
  }

  getInitial(name: string): string {
    return name ? name.charAt(0).toUpperCase() : '';
  }

  private extractSectionContent(feedback: string, sectionHeader: string, nextSectionHeaders: string[]): string {
    if (!feedback) return '';

    const feedbackLower = feedback.toLowerCase();
    const headerLower = sectionHeader.toLowerCase();
    const sectionStart = feedbackLower.indexOf(headerLower);

    if (sectionStart === -1) {
      console.log(`Section "${sectionHeader}" not found`);
      return '';
    }

    const contentStart = sectionStart + sectionHeader.length;

    let sectionEnd = feedback.length;
    for (const nextHeader of nextSectionHeaders) {
      const nextHeaderLower = nextHeader.toLowerCase();
      const nextHeaderPos = feedbackLower.indexOf(nextHeaderLower, contentStart);
      if (nextHeaderPos !== -1 && nextHeaderPos < sectionEnd) {
        sectionEnd = nextHeaderPos;
      }
    }

    return feedback.substring(contentStart, sectionEnd).trim();
  }

  private cleanTextContent(text: string): string {
    if (!text) return '';

    let cleaned = text.replace(/\. \./g, '.');

    while (cleaned.endsWith('.') && cleaned.endsWith('..')) {
      cleaned = cleaned.slice(0, -1);
    }

    return cleaned.trim();
  }

  parsedJudgeFeedback(feedback: string): {
    rapper1Analysis: string,
    rapper2Analysis: string,
    comparison: string
  } | null {
    if (!feedback || !this.battle) return null;

    const result = {
      rapper1Analysis: '',
      rapper2Analysis: '',
      comparison: ''
    };

    const rapper1Header = `Analysis of ${this.battle.rapper1_name}:`;
    const rapper2Header = `Analysis of ${this.battle.rapper2_name}:`;
    const comparisonHeader = "Comparison:";

    const allHeaders = [rapper1Header, rapper2Header, comparisonHeader];

    result.rapper1Analysis = this.extractSectionContent(
      feedback,
      rapper1Header,
      allHeaders.slice(allHeaders.indexOf(rapper1Header) + 1)
    );

    result.rapper2Analysis = this.extractSectionContent(
      feedback,
      rapper2Header,
      allHeaders.slice(allHeaders.indexOf(rapper2Header) + 1)
    );

    result.comparison = this.extractSectionContent(
      feedback,
      comparisonHeader,
      []
    );

    result.rapper1Analysis = this.cleanTextContent(result.rapper1Analysis);
    result.rapper2Analysis = this.cleanTextContent(result.rapper2Analysis);
    result.comparison = this.cleanTextContent(result.comparison);
    return result;
  }

  initCollapsedState(roundId: string): void {
    if (!this.collapsedAnalysis[roundId]) {
      this.collapsedAnalysis[roundId] = {
        rapper1: true,
        rapper2: true,
        comparison: true
      };
    }
  }

  toggleAnalysisSection(roundId: string, section: 'rapper1' | 'rapper2' | 'comparison'): void {
    this.initCollapsedState(roundId);
    this.collapsedAnalysis[roundId][section] = !this.collapsedAnalysis[roundId][section];
  }

  isCollapsed(roundId: string, section: 'rapper1' | 'rapper2' | 'comparison'): boolean {
    this.initCollapsedState(roundId);
    return this.collapsedAnalysis[roundId][section];
  }
}
