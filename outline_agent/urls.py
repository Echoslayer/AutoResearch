from django.urls import path
from . import views
from . import api

urlpatterns = [
    # Main outline generation view
    path('generate/', views.generate_outline, name='generate_outline'),
    path('get/<int:id>/', views.get_outline, name='get_outline'),

    # API endpoints
    path('api/retrieve_papers/', api.retrieve_papers, name='retrieve_papers'),
    path('api/chunk_papers/', api.chunk_papers, name='chunk_papers'),
    path('api/generate_rough_outlines/', api.generate_rough_outlines, name='generate_rough_outlines'),
    path('api/merge_outlines/', api.merge_outlines, name='merge_outlines'),
    path('api/generate_subsection_outlines/', api.generate_subsection_outlines, name='generate_subsection_outlines'),
    path('api/process_outlines/', api.process_outlines, name='process_outlines'),
    path('api/edit_final_outline/', api.edit_final_outline, name='edit_final_outline'),

    # Possible additional views
    path('list/', views.list_outlines, name='list_outlines'),
    path('delete/<int:id>/', views.delete_outline, name='delete_outline'),
    path('update/<int:id>/', views.update_outline, name='update_outline'),
]
