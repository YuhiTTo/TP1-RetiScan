import { ComponentFixture, TestBed } from '@angular/core/testing';

import { RetinographyUpload } from './retinography-upload';

describe('RetinographyUpload', () => {
  let component: RetinographyUpload;
  let fixture: ComponentFixture<RetinographyUpload>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [RetinographyUpload],
    }).compileComponents();

    fixture = TestBed.createComponent(RetinographyUpload);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
