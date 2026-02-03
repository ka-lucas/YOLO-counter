from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from apps.cameras.models import Camera
from .models import ModelConfiguration
from .form import ModelUploadForm


def can_delete_model(user, model):
    """Verifica se o usuário pode deletar um modelo
    Regra: Cada usuário só pode deletar modelos que ele mesmo subiu
    """
    # Apenas o proprietário do modelo pode deletar (não há exceção para admin)
    return model.uploaded_by == user


def can_edit_model(user, model):
    """Verifica se o usuário pode editar um modelo
    Regra: 
    - Apenas o proprietário do modelo pode editar seus próprios modelos
    - Se o modelo foi subido pelo superadmin, não pode ser editado por ninguém
    """
    # Se o modelo foi subido pelo superadmin, ninguém pode editar
    if model.uploaded_by and model.uploaded_by.is_superuser:
        return False
    
    # Apenas o proprietário do modelo (que não é superadmin) pode editar
    return model.uploaded_by == user and not user.is_superuser


@login_required
def index(request):
    """Página de configurações com lista de câmeras integrada"""
    cameras = Camera.objects.filter(user=request.user).order_by("-created_at")
    
    # Modelos do próprio usuário + modelos públicos
    user_models = ModelConfiguration.objects.filter(uploaded_by=request.user).order_by('-uploaded_at')
    public_models = ModelConfiguration.objects.filter(is_public=True, uploaded_by__isnull=False).exclude(uploaded_by=request.user).order_by('-uploaded_at')
    
    # Combina as duas listas
    all_models = list(user_models) + list(public_models)
    all_models.sort(key=lambda x: x.uploaded_at, reverse=True)
    
    # Busca o modelo ativo
    active_model = ModelConfiguration.objects.filter(is_active=True).first()
    
    form = ModelUploadForm()
    
    # Adiciona flag de permissão para cada modelo
    for model in all_models:
        model.can_delete = can_delete_model(request.user, model) and not model.is_active
        model.can_edit = can_edit_model(request.user, model)
    
    context = {
        "cameras": cameras,
        "models": all_models,
        "active_model": active_model,
        "form": form,
    }
    return render(request, "configuracao/index.html", context)


@login_required
def models_list(request):
    """Lista os modelos do usuário (subidos por ele)"""
    user_models = ModelConfiguration.objects.filter(uploaded_by=request.user).order_by('-uploaded_at')
    active_model = ModelConfiguration.objects.filter(is_active=True).first()
    
    context = {
        'models': user_models,
        'active_model': active_model,
    }
    return render(request, 'configuracao/models_list.html', context)


@login_required
def model_edit(request, pk):
    """Edita um modelo (apenas o proprietário pode editar)"""
    try:
        model = ModelConfiguration.objects.get(pk=pk)
    except ModelConfiguration.DoesNotExist:
        messages.error(request, 'Modelo não encontrado.')
        return redirect('configuracao:index')
    
    # Verifica permissão
    if not can_edit_model(request.user, model):
        messages.error(request, 'Você não tem permissão para editar este modelo.')
        return redirect('configuracao:index')
    
    if request.method == 'POST':
        try:
            # Atualiza nome e confiança
            model.name = request.POST.get('name', model.name).strip()
            if not model.name:
                messages.error(request, 'Nome do modelo não pode estar vazio.')
                return redirect('configuracao:model_edit', pk=pk)
            
            model.confidence_threshold = float(request.POST.get('confidence_threshold', model.confidence_threshold))
            model.is_public = request.POST.get('is_public') == 'on'
            
            model.save()
            messages.success(request, f'Modelo "{model.name}" atualizado com sucesso!')
            return redirect('configuracao:index')
        except ValueError:
            messages.error(request, 'Valor de confiança inválido.')
            return redirect('configuracao:model_edit', pk=pk)
        except Exception as e:
            messages.error(request, f'Erro ao atualizar modelo: {str(e)}')
            return redirect('configuracao:model_edit', pk=pk)
    
    context = {
        'model': model,
    }
    return render(request, 'configuracao/model_edit.html', context)


@login_required
def model_delete(request, pk):
    """Deleta um modelo (apenas o proprietário pode deletar)"""
    try:
        model = ModelConfiguration.objects.get(pk=pk)
    except ModelConfiguration.DoesNotExist:
        messages.error(request, 'Modelo não encontrado.')
        return redirect('configuracao:index')
    
    # Verifica permissão
    if not can_delete_model(request.user, model):
        messages.error(request, 'Você não tem permissão para deletar este modelo.')
        return redirect('configuracao:index')
    
    if model.is_active:
        messages.error(request, 'Não é possível deletar o modelo ativo. Ative outro modelo primeiro.')
        return redirect('configuracao:index')
    
    if request.method == 'POST':
        try:
            model_name = model.name
            model.delete()
            messages.success(request, f'Modelo "{model_name}" deletado com sucesso!')
            return redirect('configuracao:index')
        except Exception as e:
            messages.error(request, f'Erro ao deletar modelo: {str(e)}')
            return redirect('configuracao:model_delete', pk=pk)
    
    context = {
        'model': model,
    }
    return render(request, 'configuracao/model_delete.html', context)
@login_required
def upload_model(request):
    if request.method == 'POST':
        form = ModelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            model = form.save(commit=False)
            model.uploaded_by = request.user
            
            # Se não há modelo ativo, ativa este automaticamente
            if not ModelConfiguration.objects.filter(is_active=True).exists():
                model.is_active = True
            else:
                model.is_active = False
                
            model.save()
            
            status_msg = "ativado" if model.is_active else "enviado"
            messages.success(request, f'Modelo "{model.name}" {status_msg} com sucesso!')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    return redirect('configuracao:index')


@login_required
def update_model_confidence(request):
    """Atualiza a confiança do modelo ativo"""
    if request.method == 'POST':
        try:
            confidence = float(request.POST.get('confidence', 85)) / 100
            
            active_model = ModelConfiguration.objects.filter(is_active=True).first()
            if active_model:
                active_model.confidence_threshold = confidence
                active_model.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Confiança atualizada'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Nenhum modelo ativo encontrado'
                }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
    
    return JsonResponse({'success': False}, status=400)


@login_required
def toggle_model_active(request, pk):
    """Ativa/desativa um modelo"""
    if request.method == 'POST':
        model = get_object_or_404(ModelConfiguration, pk=pk)
        
        if model.is_active:
            # Desativar modelo atual
            model.is_active = False
            model.save()
            messages.success(request, f'Modelo "{model.name}" desativado.')
        else:
            # Desativar todos os outros e ativar este
            ModelConfiguration.objects.filter(is_active=True).update(is_active=False)
            model.is_active = True
            model.save()
            messages.success(request, f'Modelo "{model.name}" ativado.')
    
    return redirect('configuracao:index')