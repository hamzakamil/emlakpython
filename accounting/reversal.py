class ReversalService:
    """POSTED fiş için ters/koreksiyon işlemleri (Kural 23-24)."""

    @staticmethod
    @transaction.atomic
    def create_reversal(fis_id, reversed_by_user, reason=""):
        try:
            original_fis = MuhasebeFisi.objects.select_for_update().get(
                id=fis_id, durum=MuhasebeFisi.Durum.POSTED
            )
            count = MuhasebeFisi.objects.filter(
                tenant_id=original_fis.tenant_id
            ).count()
            reversal_no = f"MF-{timezone.now().year}-{count + 1:06d}"
            reversal_fis = MuhasebeFisi.objects.create(
                fis_no=reversal_no,
                fis_tarihi=timezone.now().date(),
                aciklama=f"TERS KAYIT: {original_fis.aciklama}",
                durum=MuhasebeFisi.Durum.POSTED,
                source_type="REVERSAL",
                source_id=original_fis.id,
                tenant_id=original_fis.tenant_id,
                created_by=reversed_by_user,
            )
            original_fis.reversed_voucher_id = reversal_fis.id
            original_fis.save()
            return {
                "success": True,
                "reversal_fis_no": reversal_fis.fis_no,
                "original_fis_no": original_fis.fis_no,
                "message": "Ters kayıt oluşturuldu",
            }
        except MuhasebeFisi.DoesNotExist:
            return {"success": False, "message": "Fiş yok veya POSTED değil"}
        except Exception as e:
            transaction.set_rollback(True)
            return {"success": False, "error": str(e), "message": "Hata"}

    @staticmethod
    @transaction.atomic
    def create_correction(fis_id, corrected_by_user, new_satirlar, description=""):
        try:
            original_fis = MuhasebeFisi.objects.get(id=fis_id, durum=MuhasebeFisi.Durum.POSTED)
            total_borc = sum(s["borc"] for s in new_satirlar)
            total_alacak = sum(s["alacak"] for s in new_satirlar)
            if total_borc != total_alacak:
                raise ValidationError("Borç != Alacak")
            count = MuhasebeFisi.objects.filter(
                tenant_id=original_fis.tenant_id
            ).count()
            correction_no = f"MF-{timezone.now().year}-{count + 1:06d}"
            correction_fis = MuhasebeFisi.objects.create(
                fis_no=correction_no,
                fis_tarihi=timezone.now().date(),
                aciklama=f"DÜZELTME: {original_fis.aciklama}",
                durum=MuhasebeFisi.Durum.POSTED,
                source_type="CORRECTION",
                source_id=original_fis.id,
                tenant_id=original_fis.tenant_id,
                created_by=corrected_by_user,
            )
            for s in new_satirlar:
                FisSatiri.objects.create(fis=correction_fis, **s)
            original_fis.correction_of = correction_fis.id
            original_fis.save()
            return {
                "success": True,
                "correction_fis_no": correction_fis.fis_no,
                "original_fis_no": original_fis.fis_no,
                "message": "Düzeltme fişi oluşturuldu",
            }
        except MuhasebeFisi.DoesNotExist:
            return {"success": False, "message": "Orijinal fiş yok"}
        except ValidationError as e:
            return {"success": False, "error": str(e), "message": "Validation hatası"}
        except Exception as e:
            transaction.set_rollback(True)
            return {"success": False, "error": str(e), "message": "Hata"}
