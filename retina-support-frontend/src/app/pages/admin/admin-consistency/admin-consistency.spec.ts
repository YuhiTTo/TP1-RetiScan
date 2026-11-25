import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { describe, expect, it, vi } from 'vitest';

import { AdminConsistency } from './admin-consistency';

import {
  AdminConsistencyIssue,
  AdminConsistencyItem,
  AdminConsistencyService
} from '../../../core/services/admin-consistency';

describe('US-22: Detalle de incidencias', () => {

  async function prepare(issues: AdminConsistencyIssue[]) {

    const record: AdminConsistencyItem = {
      id_evaluacion: 9001,
      id_establecimiento: 1,
      establecimiento: 'Establecimiento de prueba',
      consistencia: issues.length > 0
        ? 'REQUIERE_ATENCION'
        : 'CONSISTENTE',
      incidencias: issues
    };

    const mockService = {
      list: vi.fn().mockReturnValue(
        of({
          items: [record],
          total: 1,
          page: 1,
          page_size: 8,
          total_pages: 1
        })
      ),
      summary: vi.fn().mockReturnValue(
        of({
          registros_revisados: 1,
          con_incidencias: issues.length > 0 ? 1 : 0
        })
      )
    };

    await TestBed.configureTestingModule({
      imports: [AdminConsistency],
      providers: [
        provideRouter([]),
        {
          provide: AdminConsistencyService,
          useValue: mockService
        }
      ]
    }).compileComponents();

    const fixture =
      TestBed.createComponent(AdminConsistency);

    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    return { fixture, record, mockService };
  }

  it('muestra Sin incidencias cuando no existen problemas',
    async () => {

      const { fixture } = await prepare([]);

      const element: HTMLElement =
        fixture.nativeElement;

      expect(element.textContent).toContain(
        'Sin incidencias'
      );

      expect(
        element.querySelector(
          '.consistency-detail-button'
        )
      ).toBeNull();

      fixture.destroy();
    }
  );

  it('abre, muestra y cierra el detalle de CONS-03',
    async () => {

      const { fixture } = await prepare([
        {
          codigo: 'CONS-03',
          descripcion:
            'Evaluación finalizada sin fecha de finalización.'
        }
      ]);

      const element: HTMLElement =
        fixture.nativeElement;

      const button = element.querySelector(
        '.consistency-detail-button'
      ) as HTMLButtonElement | null;

      const dialog = element.querySelector(
        '.consistency-dialog'
      ) as HTMLDialogElement | null;

      expect(button).not.toBeNull();
      expect(dialog).not.toBeNull();

      if (!button || !dialog) {
        throw new Error(
          'No se encontro el boton o la ventana.'
        );
      }

      const showModalMock = vi.fn();
      const closeMock = vi.fn();

      Object.defineProperty(dialog, 'showModal', {
        configurable: true,
        value: showModalMock
      });

      Object.defineProperty(dialog, 'close', {
        configurable: true,
        value: closeMock
      });

      button.click();
      fixture.detectChanges();

      expect(showModalMock).toHaveBeenCalledOnce();

      expect(dialog.textContent).toContain(
        'CONS-03'
      );

      expect(dialog.textContent).toContain(
        'Evaluación finalizada sin fecha de finalización.'
      );

      const closeButton = dialog.querySelector(
        '.consistency-dialog-actions button'
      ) as HTMLButtonElement | null;

      expect(closeButton).not.toBeNull();

      if (!closeButton) {
        throw new Error(
          'No se encontro el boton Cerrar.'
        );
      }

      closeButton.click();

      expect(closeMock).toHaveBeenCalledOnce();

      dialog.dispatchEvent(new Event('close'));
      fixture.detectChanges();

      expect(
        fixture.componentInstance.selectedRecord
      ).toBeNull();

      fixture.destroy();
    }
  );

});
