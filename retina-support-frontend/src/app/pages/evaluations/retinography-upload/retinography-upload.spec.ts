import { ComponentFixture, TestBed } from '@angular/core/testing';
import {
  ActivatedRoute,
  convertToParamMap,
  provideRouter
} from '@angular/router';

import { RetinographyUpload } from './retinography-upload';
import {
  EvaluationService
} from '../../../core/services/evaluation';

describe('RetinographyUpload', () => {
  let component: RetinographyUpload;
  let fixture: ComponentFixture<RetinographyUpload>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [RetinographyUpload],
      providers: [
        provideRouter([]),
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {
              paramMap: convertToParamMap({})
            }
          }
        },
        {
          provide: EvaluationService,
          useValue: {
            getEvaluationDetail: () => {
              throw new Error(
                'La prueba no debe consultar evaluaciones reales.'
              );
            }
          }
        }
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(RetinographyUpload);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
